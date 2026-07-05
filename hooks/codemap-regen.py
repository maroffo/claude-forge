#!/usr/bin/env python3
# ABOUTME: PostToolUse hook — regenerates CODEMAP.md after git commit in repos that opted in
# ABOUTME: Opt-in marker is an existing CODEMAP.md; regeneration is deterministic and fail-open

import json
import os
import re
import subprocess
import sys

COMMIT_RE = re.compile(r"(^|[;&|\s])git\s+(-C\s+\S+\s+)?commit(\s|$)")


def commit_target(cmd, fallback):
    """Honor `git -C <path> commit` and leading `cd <path> &&` forms."""
    m = re.search(r"git\s+-C\s+(\S+)\s+commit", cmd)
    if m:
        return os.path.expanduser(m.group(1))
    m = re.match(r"\s*cd\s+(\S+)\s*&&", cmd)
    if m:
        return os.path.expanduser(m.group(1))
    return fallback


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    cmd = (payload.get("tool_input") or {}).get("command", "")
    if not COMMIT_RE.search(cmd):
        sys.exit(0)

    repo = commit_target(cmd, payload.get("cwd") or os.getcwd())
    codemap = os.path.join(repo, "CODEMAP.md")
    if not os.path.isfile(codemap):
        sys.exit(0)  # repo has not opted in

    generator = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "codemap", "generate.py")
    if not os.path.isfile(generator):
        sys.exit(0)

    try:
        subprocess.run(
            ["uv", "run", "--no-project", "python3", generator, "--repo", repo],
            capture_output=True, text=True, timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
