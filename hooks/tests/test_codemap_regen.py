#!/usr/bin/env python3
# ABOUTME: Tests for codemap-regen.py — commit in an opted-in repo regenerates CODEMAP.md
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_codemap_regen.py (requires sg + uv)

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "codemap-regen.py")


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True)


def make_repo():
    d = tempfile.mkdtemp(prefix="codemap-regen-")
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    with open(os.path.join(d, "main.go"), "w") as fh:
        fh.write('package main\n\nfunc routes(r Router) {\n\tr.Get("/ping", pong)\n}\n')
    git(d, "add", ".")
    git(d, "commit", "-qm", "seed")
    return d


def run_hook(cwd, command):
    payload = json.dumps(
        {"hook_event_name": "PostToolUse", "cwd": cwd, "tool_input": {"command": command}}
    )
    proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return proc


def main():
    if not shutil.which("sg") or not shutil.which("uv"):
        sys.exit("FAIL  codemap-regen: needs sg + uv on PATH (the hook re-runs the generator via uv)")

    # 1. Opted-in repo (CODEMAP.md exists), git commit -> map regenerated at HEAD
    repo = make_repo()
    with open(os.path.join(repo, "CODEMAP.md"), "w") as fh:
        fh.write("<!-- codemap: 0000000 old v1 -->\nstale content\n")
    run_hook(repo, "git commit -m 'x'")
    text = open(os.path.join(repo, "CODEMAP.md")).read()
    head = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert head in text.splitlines()[0], f"stamp not refreshed: {text.splitlines()[0]}"
    assert "/ping" in text, f"regenerated map missing endpoint: {text}"

    # 2. Repo without CODEMAP.md -> untouched (no opt-in)
    repo2 = make_repo()
    run_hook(repo2, "git commit -m 'x'")
    assert not os.path.exists(os.path.join(repo2, "CODEMAP.md")), "must not create maps uninvited"

    # 3. Non-commit command -> no-op even when opted in
    with open(os.path.join(repo2, "CODEMAP.md"), "w") as fh:
        fh.write("<!-- codemap: 0000000 old v1 -->\nkeep me\n")
    run_hook(repo2, "git status")
    assert "keep me" in open(os.path.join(repo2, "CODEMAP.md")).read()

    # 4. git -C <path> commit form resolves the target repo
    repo3 = make_repo()
    with open(os.path.join(repo3, "CODEMAP.md"), "w") as fh:
        fh.write("<!-- codemap: 0000000 old v1 -->\nstale\n")
    run_hook("/", f"git -C {repo3} commit -m 'x'")
    assert "/ping" in open(os.path.join(repo3, "CODEMAP.md")).read(), "-C target not honored"

    # 5. `cd <path> && git commit` form resolves the target repo
    repo4 = make_repo()
    with open(os.path.join(repo4, "CODEMAP.md"), "w") as fh:
        fh.write("<!-- codemap: 0000000 old v1 -->\nstale\n")
    run_hook("/", f"cd {repo4} && git commit -m 'x'")
    assert "/ping" in open(os.path.join(repo4, "CODEMAP.md")).read(), "cd-prefix target not honored"

    # 6. Garbage payload -> exit 0
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0

    print("PASS  codemap-regen (6 cases)")


if __name__ == "__main__":
    main()
