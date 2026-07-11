#!/usr/bin/env python3
# ABOUTME: Regression tests for the commit-gate trigger regex (git -C form), jq fail-closed, and --no-verify deny
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_commit_gates.py

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.join(os.path.dirname(__file__), "..")


def run_sh(script, command, cwd=None):
    payload = json.dumps({"tool_input": {"command": command}})
    proc = subprocess.run(
        ["bash", os.path.join(HOOKS, script)],
        input=payload, capture_output=True, text=True, timeout=60, cwd=cwd,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def run_py(script, command, cwd=None):
    proc = subprocess.run(
        [sys.executable, os.path.join(HOOKS, script)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True, text=True, timeout=60, cwd=cwd,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def is_deny(result):
    return bool(result) and result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def make_repo(branch):
    d = tempfile.mkdtemp(prefix="gate-test-")
    subprocess.run(["git", "init", "-b", branch, d], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", d, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "--allow-empty", "-m", "init"],
        capture_output=True, check=True,
    )
    return d


def main():
    main_repo = make_repo("main")
    feat_repo = make_repo("feat/x")
    try:
        # main-branch-guard: plain form on main (cwd) still denies
        assert is_deny(run_sh("main-branch-guard.sh", 'git commit -m "feat: x"', cwd=main_repo)), "plain-on-main"
        # git -C form previously bypassed ALL gates (regression for the audit SEVERE)
        assert is_deny(run_sh("main-branch-guard.sh", f'git -C {main_repo} commit -m "feat: x"')), "git-C-on-main"
        # cd form resolves too
        assert is_deny(run_sh("main-branch-guard.sh", f'cd {main_repo} && git commit -m "feat: x"')), "cd-on-main"
        # feature branch passes
        assert run_sh("main-branch-guard.sh", f'git -C {feat_repo} commit -m "feat: x"') is None, "feature-branch-ok"
        # non-commit commands ignored
        assert run_sh("main-branch-guard.sh", "git log --grep commit") is None, "non-commit-ignored"
        assert run_sh("main-branch-guard.sh", "git commit-tree abc") is None, "commit-tree-ignored"
        # chained checkout -b before the commit lands on the NEW branch: allow even from main
        assert run_sh("main-branch-guard.sh", 'git checkout -b feat/y && git commit -m "feat: x"', cwd=main_repo) is None, "checkout-chain-ok"
        assert run_sh("main-branch-guard.sh", 'git switch -c feat/y && git commit -m "feat: x"', cwd=main_repo) is None, "switch-chain-ok"
        # ...but chaining INTO main still denies
        assert is_deny(run_sh("main-branch-guard.sh", 'git checkout -b main && git commit -m "feat: x"', cwd=feat_repo)), "checkout-chain-to-main"
        # a branch name mentioned only inside the commit message does not spoof the check
        assert is_deny(run_sh("main-branch-guard.sh", 'git commit -m "feat: mention git checkout -b feat/z"', cwd=main_repo)), "spoof-in-message"

        # pre-commit-gate: -C into a repo with no Makefile must fire and deny
        assert is_deny(run_sh("pre-commit-gate.sh", f'git -C {feat_repo} commit -m "feat: x"')), "gate-git-C-fires"
        assert run_sh("pre-commit-gate.sh", "ls -la") is None, "gate-non-commit-ignored"

        # commit-intent-guard: -C form triggers message validation
        assert is_deny(run_py("commit-intent-guard.py", f'git -C {feat_repo} commit -m "bad message"', cwd=feat_repo)), "intent-git-C-bad-msg"
        # bypass flags are denied even with a conventional message
        for flag in ("--no-verify", "--no-hooks", "--no-pre-commit-hook"):
            assert is_deny(run_py("commit-intent-guard.py", f'git commit {flag} -m "feat: x"', cwd=feat_repo)), f"bypass:{flag}"
        # clean conventional commit passes
        assert run_py("commit-intent-guard.py", 'git commit -m "feat: ok"', cwd=feat_repo) is None, "intent-clean-ok"

        # stub scan: "placeholder" fires only in stub-intent form, not as domain
        # vocabulary (contract: 2026-07-11_commit-intent-guard-placeholder-fp)
        def staged(content):
            path = os.path.join(feat_repo, "scan.go")
            with open(path, "w") as f:
                f.write(content + "\n")
            subprocess.run(["git", "-C", feat_repo, "add", "scan.go"], capture_output=True, check=True)
            result = run_py("commit-intent-guard.py", 'git commit -m "feat: ok"', cwd=feat_repo)
            subprocess.run(["git", "-C", feat_repo, "reset"], capture_output=True, check=True)
            return result

        for stub in (
            "// placeholder",
            "// placeholder: wire the real parser",
            "// placeholder for the real implementation",
            "// placeholder implementation",
            "// TODO fix this",
        ):
            assert is_deny(staged(stub)), f"stub-denied:{stub}"
        for legit in (
            "// placeholder and its presence marks the region for replacement",
            "// the placeholder appears while the raw text block is redacted",
            "// entity replaced by its [ENTITY_TYPE] placeholder",
        ):
            assert staged(legit) is None, f"domain-vocab-ok:{legit}"

        # stale-index on index-mutating commands: the scan must judge what the
        # command WILL commit, not the pre-add index
        # (contract: 2026-07-11_commit-intent-guard-stale-index.md)
        def git(*args):
            subprocess.run(["git", "-C", feat_repo, *args], capture_output=True, check=True)

        def write(name, content):
            with open(os.path.join(feat_repo, name), "w") as f:
                f.write(content + "\n")

        def clean_repo():
            git("reset", "--hard", "HEAD")
            git("clean", "-fd")

        write("f.go", "// fine")
        git("add", "f.go")
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "feat: base")

        # false-deny regression: stub staged, then FIXED in worktree; the chained
        # add stages the fix, so the commit is clean and must pass
        write("f.go", "// TODO wire the real parser")
        git("add", "f.go")
        write("f.go", "// fixed for real")
        assert run_py("commit-intent-guard.py", 'git add f.go && git commit -m "feat: x"', cwd=feat_repo) is None, "stale-fix-allowed"
        clean_repo()

        # bypass closure, tracked file: stub only in the worktree, chained add
        # (or commit -a) would commit it: deny even though the index is clean
        write("f.go", "// TODO wire the real parser")
        assert is_deny(run_py("commit-intent-guard.py", 'git add f.go && git commit -m "feat: x"', cwd=feat_repo)), "bypass-add-chain-denied"
        assert is_deny(run_py("commit-intent-guard.py", 'git commit -am "feat: x"', cwd=feat_repo)), "bypass-commit-a-denied"

        # boundary: plain commit does NOT judge unstaged worktree content
        assert run_py("commit-intent-guard.py", 'git commit -m "feat: x"', cwd=feat_repo) is None, "plain-commit-ignores-worktree"
        clean_repo()

        # bypass closure, untracked file: diff HEAD cannot see it, the named-file
        # (and add .) scan must
        write("stub2.go", "// placeholder: implement")
        assert is_deny(run_py("commit-intent-guard.py", 'git add stub2.go && git commit -m "feat: x"', cwd=feat_repo)), "bypass-untracked-named-denied"
        assert is_deny(run_py("commit-intent-guard.py", 'git add . && git commit -m "feat: x"', cwd=feat_repo)), "bypass-untracked-dot-denied"
        git("clean", "-fd")
    finally:
        shutil.rmtree(main_repo, ignore_errors=True)
        shutil.rmtree(feat_repo, ignore_errors=True)

    print("PASS  commit-gates (30 cases)")


if __name__ == "__main__":
    main()
