#!/usr/bin/env python3
# ABOUTME: Tests for gitignore-anchor-lint.py — bare-name swallow warning, anchored/glob silence, .env negation
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_gitignore_anchor_lint.py

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "gitignore-anchor-lint.py")


def git(repo, *args):
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   capture_output=True, check=True)


def make_repo():
    d = tempfile.mkdtemp(prefix="gil-test-")
    subprocess.run(["git", "init", "-b", "main", d], capture_output=True, check=True)
    os.makedirs(os.path.join(d, "cmd", "golem"))
    with open(os.path.join(d, "cmd", "golem", "main.go"), "w") as fh:
        fh.write("package main\n")
    git(d, "add", ".")
    git(d, "commit", "-m", "init")
    return d


def run_hook(repo, gitignore_lines):
    with open(os.path.join(repo, ".gitignore"), "w") as fh:
        fh.write("\n".join(gitignore_lines) + "\n")
    git(repo, "add", ".gitignore")
    payload = json.dumps({"tool_input": {"command": 'git commit -m "chore: ignore"'}})
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30, cwd=repo
    )
    assert proc.returncode == 0, proc.stderr
    git(repo, "reset", ".gitignore")
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def ctx(result):
    return result["hookSpecificOutput"]["additionalContext"] if result else ""


def main():
    repo = make_repo()
    try:
        # Bare name matching a tracked directory: warns, suggests anchoring
        out = run_hook(repo, ["golem"])
        assert "golem" in ctx(out) and "/golem" in ctx(out), out
        # Anchored form: silent
        assert run_hook(repo, ["/golem"]) is None, "anchored should be silent"
        # Bare name that matches nothing tracked: silent
        assert run_hook(repo, ["nonexistent-binary"]) is None, "speculative name silent"
        # Glob patterns: silent
        assert run_hook(repo, ["*.log"]) is None, "glob silent"
        assert run_hook(repo, ["node_modules/"]) is None, "dir pattern silent"
        # .env.* without negation: warns about .env.example
        out = run_hook(repo, [".env.*"])
        assert ".env.example" in ctx(out), out
        # .env.* WITH negation: silent
        assert run_hook(repo, [".env.*", "!.env.example"]) is None, "negated env silent"
        # Never a deny: even the warning is additionalContext only
        out = run_hook(repo, ["golem"])
        assert "permissionDecision" not in json.dumps(out), "must never deny"
        # Non-commit command ignored
        payload = json.dumps({"tool_input": {"command": "ls"}})
        proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30, cwd=repo)
        assert proc.returncode == 0 and not proc.stdout.strip(), "non-commit ignored"
    finally:
        shutil.rmtree(repo, ignore_errors=True)

    print("PASS  gitignore-anchor-lint (9 cases)")


if __name__ == "__main__":
    main()
