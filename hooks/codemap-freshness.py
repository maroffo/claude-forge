#!/usr/bin/env python3
# ABOUTME: SessionStart hook — advisory when CODEMAP.md's commit stamp is behind HEAD for covered files
# ABOUTME: Staleness must be detectable, never assumed; advisory only, fail-open on any error

import json
import os
import re
import subprocess
import sys

STAMP_RE = re.compile(r"<!--\s*codemap:\s*(\S+)")
# Extensions/files the map derives from; changes elsewhere don't stale it.
COVERED_EXTS = {".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".proto"}
COVERED_FILES = {"pnpm-workspace.yaml", "package.json", "go.mod", "pyproject.toml"}


def covered(path):
    return os.path.splitext(path)[1] in COVERED_EXTS or os.path.basename(path) in COVERED_FILES


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    codemap = os.path.join(cwd, "CODEMAP.md")
    if not os.path.isfile(codemap):
        sys.exit(0)

    try:
        first_line = open(codemap, encoding="utf-8", errors="ignore").readline()
    except OSError:
        sys.exit(0)

    m = STAMP_RE.search(first_line)
    if not m:
        print("codemap-freshness: CODEMAP.md has no readable stamp; regenerate it (make codemap) before relying on it.")
        sys.exit(0)
    sha = m.group(1)
    if sha == "unversioned":
        sys.exit(0)

    try:
        diff = subprocess.run(
            ["git", "-C", cwd, "diff", "--name-only", f"{sha}..HEAD"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        sys.exit(0)
    if diff.returncode != 0:
        # Stamp SHA unknown to this clone (rebase, gc): unverifiable, say so.
        print(f"codemap-freshness: CODEMAP.md stamp {sha} is not in this history; regenerate it (make codemap).")
        sys.exit(0)

    stale = sorted(p for p in diff.stdout.splitlines() if covered(p))
    if stale:
        sample = ", ".join(stale[:3]) + (", ..." if len(stale) > 3 else "")
        print(
            f"codemap-freshness: CODEMAP.md was generated at {sha}; {len(stale)} covered file(s) "
            f"changed since ({sample}). Treat the map as stale evidence: regenerate it (make codemap) "
            f"before relying on it."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
