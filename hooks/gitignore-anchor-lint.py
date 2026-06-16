#!/usr/bin/env python3
# ABOUTME: PreToolUse advisory hook, flags bare-name .gitignore lines that silently swallow tracked source
# ABOUTME: Warns to anchor with a leading slash, and on .env.* globs missing a .env.example negation

"""Advisory pre-commit lint for newly-added .gitignore lines.

Targets the recurring "where did my file go" class (Pattern 4 in the learning
corpus): a bare project/binary name like `golem` or `mirsad` in .gitignore is a
glob that matches a same-named directory at any depth (e.g. `cmd/golem/main.go`),
silently excluding source. The fix is to anchor it: `/golem`. Also flags `.env.*`
style globs that lack a `!.env.example` exception, which eat the template file.

Advisory only: emits additionalContext, never blocks the commit.
"""

import json
import re
import subprocess
import sys

GLOB_CHARS = set("*?[]!")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def staged_gitignore_files():
    r = sh("git diff --cached --name-only --diff-filter=ACM")
    return [p for p in r.stdout.splitlines() if p == ".gitignore" or p.endswith("/.gitignore")]


def added_lines(path):
    """Newly-added (+) content lines for one staged .gitignore, comments/blanks stripped."""
    diff = sh(f"git diff --cached -- {path}").stdout
    out = []
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:].strip()
        if not body or body.startswith("#"):
            continue
        out.append(body)
    return out


def tracked_path_segments():
    """Set of path segments across tracked files, so we only warn when a bare
    name would actually swallow something real (a dir or file that exists)."""
    r = sh("git ls-files")
    segs = set()
    for p in r.stdout.splitlines():
        parts = p.split("/")
        segs.update(parts[:-1])      # directory segments
        segs.add(parts[-1])          # filename
    return segs


def is_bare_name(line):
    """A glob with no anchoring: no leading slash, no embedded slash, no glob metachar."""
    if line.startswith("/") or "/" in line:
        return False
    if any(c in GLOB_CHARS for c in line):
        return False
    return True


def lint(path, lines, segments):
    warnings = []
    gitignore_text = sh(f"git show :{path}").stdout  # staged content, for negation lookups
    has_envexample_negation = bool(
        re.search(r"^\s*!.*\.env\.example", gitignore_text, re.M)
    )
    for line in lines:
        # 1. Bare name that matches an existing tracked directory/file segment.
        if is_bare_name(line) and line in segments:
            warnings.append(
                f"`{line}` is unanchored: it matches any path segment named "
                f"`{line}` (including a `{line}/` directory of source). "
                f"Anchor it as `/{line}` to ignore only the repo-root entry."
            )
        # 2. .env glob without a template exception.
        if re.match(r"\.env(\.\*|\*|\.\w+)?$", line) and "example" not in line:
            if not has_envexample_negation:
                warnings.append(
                    f"`{line}` will also ignore `.env.example`. Add a negation "
                    f"like `!.env.example` (or `!**/.env.example`) so the template stays tracked."
                )
    return warnings


def advise(msg):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": msg,
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

    files = staged_gitignore_files()
    if not files:
        sys.exit(0)

    segments = tracked_path_segments()
    all_warnings = []
    for path in files:
        for w in lint(path, added_lines(path), segments):
            all_warnings.append(f"{path}: {w}")

    if all_warnings:
        body = "\n".join(f"  - {w}" for w in all_warnings[:8])
        more = f"\n  ... and {len(all_warnings) - 8} more" if len(all_warnings) > 8 else ""
        advise(
            "Heads up, .gitignore patterns that may silently exclude tracked source:\n"
            + body + more
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
