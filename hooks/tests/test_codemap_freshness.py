#!/usr/bin/env python3
# ABOUTME: Tests for codemap-freshness.py — synthetic git repos through the real hook process
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_codemap_freshness.py

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "codemap-freshness.py")


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True)


def make_repo():
    d = tempfile.mkdtemp(prefix="codemap-fresh-")
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    with open(os.path.join(d, "main.go"), "w") as fh:
        fh.write("package main\n")
    git(d, "add", ".")
    git(d, "commit", "-qm", "seed")
    return d


def head(repo):
    return subprocess.run(
        ["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


def write_map(repo, sha):
    with open(os.path.join(repo, "CODEMAP.md"), "w") as fh:
        fh.write(f"<!-- codemap: {sha} 2026-07-05T00:00:00+00:00 v1 -->\n# Code Map\n")


def run_hook(cwd):
    payload = json.dumps({"hook_event_name": "SessionStart", "cwd": cwd})
    proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def main():
    # 1. Map stamped at HEAD -> silent
    repo = make_repo()
    write_map(repo, head(repo))
    assert run_hook(repo) == "", "fresh map must be silent"

    # 2. Covered file changed after stamp -> advisory names the file
    with open(os.path.join(repo, "api.go"), "w") as fh:
        fh.write("package main\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "add api")
    out = run_hook(repo)
    assert "stale" in out and "api.go" in out, f"expected staleness advisory, got: {out!r}"

    # 3. Only non-covered files changed -> silent
    repo2 = make_repo()
    write_map(repo2, head(repo2))
    with open(os.path.join(repo2, "README.md"), "w") as fh:
        fh.write("docs\n")
    git(repo2, "add", ".")
    git(repo2, "commit", "-qm", "docs only")
    assert run_hook(repo2) == "", "docs-only change must not stale the map"

    # 4. No CODEMAP.md -> silent (repo not opted in)
    repo3 = make_repo()
    assert run_hook(repo3) == "", "no map, no advisory"

    # 5. Unreadable stamp -> advisory to regenerate
    write_map(repo3, "not-a-sha")
    out = run_hook(repo3)
    assert "regenerate" in out, f"unknown sha must advise regeneration, got: {out!r}"

    with open(os.path.join(repo3, "CODEMAP.md"), "w") as fh:
        fh.write("# no stamp here\n")
    out = run_hook(repo3)
    assert "no readable stamp" in out, out

    # 6. unversioned stamp -> silent (nothing to verify against)
    write_map(repo3, "unversioned")
    assert run_hook(repo3) == "", "unversioned stamp must be silent"

    # 7. Missing/garbage payload -> exit 0, silent
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip()

    print("PASS  codemap-freshness (7 cases)")


if __name__ == "__main__":
    main()
