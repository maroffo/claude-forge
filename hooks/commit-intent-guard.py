#!/usr/bin/env python3
# ABOUTME: PreToolUse Tier A commit-intent guard (stub detection, conventional message, deletion advisory)
# ABOUTME: Deny on stub/malformed message, advisory on unplanned deletions

import fnmatch
import json
import os
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
    # "placeholder" only in stub-intent form: the bare word, followed by
    # punctuation, or followed by a stub-intent word. Descriptive mid-sentence
    # uses must pass: in redaction/templating codebases "placeholder" is domain
    # vocabulary (e.g. the [ENTITY_TYPE] placeholder), and wrapped comments can
    # put it at line start (contract: 2026-07-11_commit-intent-guard-placeholder-fp).
    (r"^placeholder\b(?:\s*$|\s*[:.\-]|\s+(?:for|until|impl\w*|code|logic|value|here|only)\b)", "placeholder"),
]
# Statement-level stubs (non-comment, detected in code context)
STATEMENT_PATTERNS = [
    (r"^\s*raise\s+NotImplementedError", "raise NotImplementedError"),
    (r"^\s*pass\s*#\s*stub\b", "stub pass"),
]

# A commit command that ALSO mutates the index (a chained `git add`, or commit
# flags that pull straight from the working tree: -a / combined short flags like
# -am, --all, --include) makes `git diff --cached` stale: PreToolUse runs BEFORE
# the command, so the index it sees is pre-add. For those commands the scan reads
# `git diff HEAD` (index + working tree) plus the untracked files the add names.
# Over-matching only widens the scan — the fail-safe direction.
# Contract: 2026-07-11_commit-intent-guard-stale-index.md
INDEX_MUTATING_RE = re.compile(
    r"\bgit\b[^|;&]*\badd\b"
    r"|\bcommit\b[^|;&]*\s-[a-zA-Z]*a[a-zA-Z]*\b"
    r"|\bcommit\b[^|;&]*\s--(?:all|include)\b"
)


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


def _skip_file(path):
    """Files where markers can legitimately appear as documentation or data."""
    return (
        any(path.endswith(sfx) for sfx in STUB_SCAN_SKIP_SUFFIXES)
        or any(p in path for p in STUB_SCAN_SKIP_PATHS)
    )


def _stub_in_line(content):
    """Return (line, label) if the line carries an unfinished-work marker, else None.
    TODO/FIXME/XXX/placeholder only in comment context (not string literals or
    documentation tables); NotImplementedError and stub-pass as statements anywhere."""
    comment = _extract_comment_body(content)
    if comment is not None:
        for pat, label in COMMENT_PATTERNS:
            if re.search(pat, comment):
                return (content.strip()[:100], label)
    for pat, label in STATEMENT_PATTERNS:
        if re.search(pat, content):
            return (content.strip()[:100], label)
    return None


def scan_added_lines_for_stubs(diff_cmd):
    """Return list of (line, label) for unfinished-work markers in ADDED diff lines.
    Markdown/docs and vendored paths are skipped. diff_cmd is `git diff --cached`
    for a plain commit, `git diff HEAD` when the command mutates the index (see
    INDEX_MUTATING_RE)."""
    diff = sh(diff_cmd).stdout
    issues = []
    current_file = None
    for line in diff.splitlines():
        m = re.match(r"^diff --git a/(\S+) b/(\S+)", line)
        if m:
            current_file = m.group(2)
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if current_file is None or _skip_file(current_file):
            continue
        hit = _stub_in_line(line[1:])
        if hit:
            issues.append(hit)
    return issues


def _add_targets(command):
    """Best-effort pathspec tokens of every chained `git add` in the command.
    `-A`/`--all` (and `.`) normalize to "." (scan every untracked file)."""
    targets = []
    for m in re.finditer(r"\bgit\b(?:\s+-C\s+\S+)?\s+add\s+([^|;&]*)", command):
        for tok in m.group(1).split():
            if tok.startswith("-"):
                if tok in ("-A", "--all"):
                    targets.append(".")
                continue
            targets.append(tok.strip("'\""))
    return targets


def scan_untracked_for_stubs(targets):
    """Scan untracked files matched by the add targets. `git diff HEAD` cannot see
    untracked content, so a chained `git add newfile && git commit` would otherwise
    stage and commit a stub the diff scan never saw."""
    if not targets:
        return []
    untracked = sh("git ls-files --others --exclude-standard").stdout.splitlines()
    issues = []
    for path in untracked:
        if _skip_file(path):
            continue
        matched = any(
            t == "." or path == t
            or path.startswith(t.rstrip("/") + "/")
            or fnmatch.fnmatch(path, t)
            for t in targets
        )
        if not matched or not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for raw in f:
                    hit = _stub_in_line(raw.rstrip("\n"))
                    if hit:
                        issues.append(hit)
                        break
        except OSError:
            continue
    return issues


def staged_deletions(diff_cmd):
    r = sh(f"{diff_cmd} --name-only --diff-filter=D")
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
    if not re.search(r"(^|[;&|\s])git\s+(-C\s+\S+\s+)?commit(\s|$)", cmd):
        sys.exit(0)
    # commit-tree etc. already excluded by the pattern above (requires space after "commit")

    # 0. Hook-bypass flags are FORBIDDEN (CLAUDE.md): deny before anything else.
    if re.search(r"--no-verify\b|--no-hooks\b|--no-pre-commit-hook\b", cmd):
        deny(
            "Hook-bypass flag detected (--no-verify / --no-hooks / "
            "--no-pre-commit-hook). These are FORBIDDEN: fix the failing hook "
            "or check systematically instead of bypassing it. Pressure is not "
            "justification."
        )

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

    # 2. Stub detection on ADDED lines. An index-mutating command (chained add,
    # commit -a/--all/--include) is judged on `git diff HEAD` + the untracked
    # files the add names, because the staged index is pre-command and stale.
    index_mutating = bool(INDEX_MUTATING_RE.search(cmd))
    diff_cmd = "git diff --cached"
    if index_mutating and sh("git rev-parse --verify -q HEAD").returncode == 0:
        diff_cmd = "git diff HEAD"  # unborn branch keeps the --cached fallback
    stubs = scan_added_lines_for_stubs(diff_cmd)
    if index_mutating:
        stubs += scan_untracked_for_stubs(_add_targets(cmd))
    if stubs:
        lines = "\n".join(f"  - {label}: `{line}`" for line, label in stubs[:5])
        more = f"\n  ... and {len(stubs) - 5} more" if len(stubs) > 5 else ""
        deny(
            "Diff introduces unfinished work (TODO/FIXME/NotImplementedError/"
            f"placeholder):\n{lines}{more}\n"
            "Either finish the work, remove the stub, or split into a separate "
            "commit with a plan entry justifying the stub."
        )

    # 3. Unplanned deletions: advisory (same stale-index reasoning as the stub scan)
    dels = staged_deletions(diff_cmd)
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
