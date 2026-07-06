#!/usr/bin/env python3
# ABOUTME: Test for the codemap CLI — running it in a fixture repo prints the map to stdout
# ABOUTME: Run with: uv run --no-project python3 codemap/tests/test_cli.py (needs sg + uv)

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "codemap.sh")


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True)


def main():
    if not shutil.which("sg") or not shutil.which("uv"):
        sys.exit("FAIL  codemap-cli: needs sg + uv on PATH")

    repo = tempfile.mkdtemp(prefix="codemap-cli-")
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    with open(os.path.join(repo, "main.go"), "w") as fh:
        fh.write('package main\n\nfunc routes(r Router) {\n\tr.Get("/ping", pong)\n}\n')
    git(repo, "add", "."); git(repo, "commit", "-qm", "seed")

    # explicit repo arg
    out = subprocess.run(["bash", CLI, repo], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "/ping" in out.stdout, f"CLI did not print the map: {out.stdout!r}"
    assert "codemap:" in out.stdout, "map should carry the generator stamp header"

    # defaults to cwd
    out = subprocess.run(["bash", CLI], cwd=repo, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0 and "/ping" in out.stdout, "CLI must default to cwd"

    # never writes a file into the repo
    assert not os.path.exists(os.path.join(repo, "CODEMAP.md")), "CLI must only print, never write into the repo"

    print("PASS  codemap-cli (1 case)")


if __name__ == "__main__":
    main()
