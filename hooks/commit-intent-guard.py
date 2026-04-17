#!/usr/bin/env python3
# ABOUTME: PreToolUse Tier A commit-intent guard (stub detection, conventional message, deletion advisory)
# ABOUTME: Deny on stub/malformed message, advisory on unplanned deletions

import json
import re
import subprocess
import sys

CONVENTIONAL_RE = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\([^)]+\))?!?: .+")

# Files where "TODO" etc. can legitimately appear as documentation or data, not stubs
STUB_SCAN_SKIP_SUFFIXES = (".md", ".txt", ".rst", ".adoc")
STUB_SCAN_SKIP_PATHS = ("/docs/", "/examples/", "/fixtures/", "/testdata/")

COMMENT_PATTERNS = [
    # Anchored: the keyword must be the first word of the comment body (after
    # the # or // marker). Otherwise meta-comments describing these keywords
    # would self-trigger.
    (r"^TODO\b", "TODO comment"),
    (r"^FIXME\b", "FIXME comment"),
    (r"^XXX\b(?!\-)", "XXX marker"),
    (r"^placeholder\b", "placeholder"),
]
# Statement-level stubs (non-comment, detected in code context)
STATEMENT_PATTERNS = [
    (r"^\s*raise\s+NotImplementedError", "raise NotImplementedError"),
    (r"^\s*pass\s*#\s*stub\b", "stub pass"),
]


def extract_commit_message(command):
    """Parse the commit message. Handles direct `-m "subject"` and heredoc
    `-m "$(cat <<'MARKER' ... MARKER\n)"` (the CLAUDE.md recommended style).
    Returns None if no message found (e.g. -F, editor mode, -m missing)."""
    # Heredoc first: looks like  <<'MARKER' ... <newline>MARKER   anywhere
    heredoc = re.search(
        r"<<\s*['\"]?(\w+)['\"]?\s*\n(.*?)\n\s*\1\s*(?:\)|$)",
        command, re.DOTALL
    )
    if heredoc:
        return heredoc.group(2).strip()
    # Direct quoted style
    quoted = re.search(r"-m\s+(['\"])(.*?)\1", command, re.DOTALL)
    if quoted:
        return quoted.group(2)
    return None


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def _extract_comment_body(content):
    """Return the comment text (after the marker) or None if there's no comment context."""
    stripped = content.lstrip()
    for marker in ("#", "//", "/*"):
        if stripped.startswith(marker):
            # Return body after the marker, with leading whitespace stripped
            return stripped[len(marker):].lstrip()
    # Inline comment (require at least one char of code before the marker)
    for marker in (" #", "\t#", " //", "\t//"):
        idx = content.find(marker)
        if idx > 0:
            tail = content[idx:].lstrip()
            m = re.match(r"^(#|//|/\*)\s*", tail)
            if m:
                return tail[m.end():]
    return None


def scan_added_lines_for_stubs():
    """Return list of (line, label) for unfinished-work markers in ADDED diff lines.
    Markdown/docs and vendored paths are skipped. TODO/FIXME/XXX/placeholder are
    only flagged when they appear in a comment context (not inside string literals
    or documentation tables). raise NotImplementedError and stub-pass are flagged
    anywhere they appear as statements.
    """
    diff = sh("git diff --cached").stdout
    issues = []
    current_file = None
    for line in diff.splitlines():
        m = re.match(r"^diff --git a/(\S+) b/(\S+)", line)
        if m:
            current_file = m.group(2)
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if current_file is None:
            continue
        if any(current_file.endswith(sfx) for sfx in STUB_SCAN_SKIP_SUFFIXES):
            continue
        if any(p in current_file for p in STUB_SCAN_SKIP_PATHS):
            continue

        content = line[1:]

        # Comment-context markers (TODO/FIXME/XXX/placeholder): only inside comments
        comment = _extract_comment_body(content)
        if comment is not None:
            for pat, label in COMMENT_PATTERNS:
                if re.search(pat, comment):
                    issues.append((content.strip()[:100], label))
                    break
        # Statement-level stubs: anywhere, but only if the whole line matches
        for pat, label in STATEMENT_PATTERNS:
            if re.search(pat, content):
                issues.append((content.strip()[:100], label))
                break
    return issues


def staged_deletions():
    r = sh("git diff --cached --name-only --diff-filter=D")
    return [p for p in r.stdout.splitlines() if p]


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }))
    sys.exit(0)


def advise(msg):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": msg
        }
    }))


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)
    cmd = payload.get("tool_input", {}).get("command", "")
    if not re.search(r"(^|[;&|\s])git\s+commit(\s|$)", cmd):
        sys.exit(0)
    # commit-tree etc. already excluded by the pattern above (requires space after "commit")

    # 1. Conventional commit message
    msg = extract_commit_message(cmd)
    if msg is None:
        # No -m flag: git will open editor; we can't validate. Let it through.
        pass
    else:
        first_line = msg.splitlines()[0].strip() if msg else ""
        if not CONVENTIONAL_RE.match(first_line):
            deny(
                "Commit message not conventional. Use: "
                "`<type>(<scope>): <subject>` where type is one of feat/fix/docs/"
                "style/refactor/perf/test/chore/ci/build/revert. "
                f"Got: `{first_line[:100]}`"
            )

    # 2. Stub detection on ADDED lines
    stubs = scan_added_lines_for_stubs()
    if stubs:
        lines = "\n".join(f"  - {label}: `{line}`" for line, label in stubs[:5])
        more = f"\n  ... and {len(stubs) - 5} more" if len(stubs) > 5 else ""
        deny(
            "Diff introduces unfinished work (TODO/FIXME/NotImplementedError/"
            f"placeholder):\n{lines}{more}\n"
            "Either finish the work, remove the stub, or split into a separate "
            "commit with a plan entry justifying the stub."
        )

    # 3. Unplanned deletions: advisory
    dels = staged_deletions()
    if dels:
        advise(
            "Heads up: this commit deletes files: "
            + ", ".join(dels[:5])
            + (" ..." if len(dels) > 5 else "")
            + ". Confirm this was intended; deletions are irreversible in the commit history."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
