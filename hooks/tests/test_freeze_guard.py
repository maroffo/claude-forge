#!/usr/bin/env python3
# ABOUTME: E2E tests for hooks/freeze-guard.sh, matrix rows 1-6 of the gstack-borrowings plan
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_freeze_guard.py

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.join(os.path.dirname(__file__), "..")
GUARD = os.path.join(HOOKS, "freeze-guard.sh")
# Absolute, so the degraded PATH of row 6 shrinks what the HOOK can find, not what
# the test can launch.
BASH = shutil.which("bash") or "bash"

# Everything the hook shells out to, minus jq, for the degraded-environment row.
BORROWED_TOOLS = ("git", "dirname", "head", "tr", "cat", "sed", "grep", "env", "uname")


def run(payload, cwd, env=None):
    """Invoke the hook with a raw stdin payload. Returns (parsed_stdout_or_None, stderr)."""
    proc = subprocess.run(
        [BASH, GUARD],
        input=payload, capture_output=True, text=True, timeout=60, cwd=cwd, env=env,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    out = proc.stdout.strip()
    return (json.loads(out) if out else None), proc.stderr


def edit(file_path, cwd, tool="Edit", env=None):
    payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": file_path}})
    return run(payload, cwd, env=env)


def is_deny(result):
    return bool(result) and result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def reason(result):
    return result["hookSpecificOutput"]["permissionDecisionReason"]


def make_repo(parent, name):
    """A real git repo with src/, docs/ and a sibling srcgen/ (the prefix-collision trap)."""
    root = os.path.join(parent, name)
    for sub in ("src", "src/deep", "docs", "srcgen"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    subprocess.run(["git", "init", "-q", root], capture_output=True, check=True)
    return root


def freeze(root, boundary_dir):
    """Write the boundary file the way skills/freeze does: physical path, trailing slash."""
    with open(os.path.join(root, ".freeze-boundary"), "w") as fh:
        fh.write(os.path.realpath(boundary_dir).rstrip("/") + "/\n")


def unfreeze(root):
    path = os.path.join(root, ".freeze-boundary")
    if os.path.exists(path):
        os.remove(path)


def bin_without_jq(parent):
    """A PATH directory holding every tool the hook needs except jq (row 6)."""
    bindir = os.path.join(parent, "bin-no-jq")
    os.makedirs(bindir, exist_ok=True)
    for tool in BORROWED_TOOLS:
        real = shutil.which(tool)
        if real:
            os.symlink(real, os.path.join(bindir, tool))
    assert shutil.which("jq", path=bindir) is None, "fixture leaks jq into the fake PATH"
    return bindir


def row_1_inside_boundary(root):
    """Boundary set, Edit inside: allow, silently. Plus the trailing-slash and exact-dir edges."""
    freeze(root, os.path.join(root, "src"))
    src = os.path.join(root, "src")

    result, err = edit(os.path.join(src, "existing_or_not.go"), cwd=root)
    assert result is None and err == "", f"in-boundary edit blocked: {result} {err}"

    result, _ = edit(os.path.join(src, "deep", "nested.go"), cwd=root)
    assert result is None, "nested in-boundary edit blocked"

    # The boundary directory itself counts as inside (exact-dir edge).
    result, _ = edit(src, cwd=root)
    assert result is None, "boundary dir itself denied"

    # A boundary written WITHOUT the trailing slash still matches inside...
    with open(os.path.join(root, ".freeze-boundary"), "w") as fh:
        fh.write(os.path.realpath(src) + "\n")
    result, _ = edit(os.path.join(src, "a.go"), cwd=root)
    assert result is None, "no-trailing-slash boundary denied an inside path"
    # ...and still does not swallow the sibling whose name it prefixes.
    result, _ = edit(os.path.join(root, "srcgen", "a.go"), cwd=root)
    assert is_deny(result), "srcgen/ passed as if inside src/ (missing trailing-slash guard)"

    # A boundary spelled through a symlink must not produce a false deny: the hook
    # resolves both sides physically before comparing.
    link = os.path.join(root, "src-link")
    if not os.path.islink(link):
        os.symlink(src, link)
    with open(os.path.join(root, ".freeze-boundary"), "w") as fh:
        fh.write(link + "/\n")
    result, err = edit(os.path.join(src, "a.go"), cwd=root)
    assert result is None, f"symlinked boundary spelling caused a false deny: {result} {err}"

    unfreeze(root)


def row_2_outside_boundary(root):
    """Boundary set, mutating tool outside: deny, naming the boundary and the remedy."""
    freeze(root, os.path.join(root, "src"))
    outside = os.path.join(root, "docs", "notes.md")

    for tool in ("Write", "Edit", "NotebookEdit"):
        result, _ = edit(outside, cwd=root, tool=tool)
        assert is_deny(result), f"{tool} outside the boundary was allowed"
        msg = reason(result)
        assert os.path.realpath(os.path.join(root, "src")) in msg, f"{tool}: boundary path absent from {msg!r}"
        assert "/freeze off" in msg, f"{tool}: remedy absent from {msg!r}"
        assert ".freeze-boundary" in msg, f"{tool}: boundary file absent from {msg!r}"

    # The session cwd is irrelevant: what matters is where the edited file lives.
    result, _ = edit(outside, cwd=os.path.join(root, "src"))
    assert is_deny(result), "deny depends on the session cwd"

    unfreeze(root)


def row_3_no_boundary(root):
    """No boundary file anywhere: allow with zero output on stdout and stderr."""
    unfreeze(root)
    for target in (os.path.join(root, "docs", "notes.md"), os.path.join(root, "src", "a.go")):
        result, err = edit(target, cwd=root)
        assert result is None, "denied with no boundary file"
        assert err == "", f"noise when inert: {err!r}"


def row_4_unparseable_path(root):
    """Boundary present, path missing or garbled: ALLOW plus one line of stderr (decision 1)."""
    freeze(root, os.path.join(root, "src"))

    def assert_allowed_with_warning(payload, label):
        result, err = run(payload, cwd=root)
        assert result is None, f"{label}: denied instead of failing open"
        assert err.strip(), f"{label}: no warning printed"
        assert len(err.strip().splitlines()) == 1, f"{label}: warning is not one line: {err!r}"
        assert "freeze-guard:" in err, f"{label}: warning is unattributed: {err!r}"

    assert_allowed_with_warning("not json at all {", "garbled JSON")
    assert_allowed_with_warning(json.dumps({"tool_input": {}}), "missing file_path")
    assert_allowed_with_warning(json.dumps({"tool_input": {"file_path": ""}}), "empty file_path")
    assert_allowed_with_warning(
        json.dumps({"tool_input": {"file_path": os.path.join(root, "docs", "a\nb.md")}}),
        "newline in file_path",
    )
    # An empty boundary file is the same class of unusable data.
    with open(os.path.join(root, ".freeze-boundary"), "w") as fh:
        fh.write("\n")
    assert_allowed_with_warning(
        json.dumps({"tool_input": {"file_path": os.path.join(root, "docs", "a.md")}}),
        "empty boundary file",
    )

    # Outside any git repo there is no boundary to consult: silent allow, no warning.
    with tempfile.TemporaryDirectory() as bare:
        result, err = run("not json at all {", cwd=bare)
        assert result is None and err == "", f"warned with no repo in sight: {err!r}"

    unfreeze(root)


def row_5_different_repo(root, other):
    """A freeze in one repo leaves every other repo alone (decision 2, boundary is repo-local)."""
    freeze(root, os.path.join(root, "src"))

    result, err = edit(os.path.join(other, "docs", "notes.md"), cwd=root)
    assert result is None and err == "", f"edit in a different repo blocked: {result} {err}"

    # Both frozen, disjoint boundaries: each repo judges its own files.
    freeze(other, os.path.join(other, "docs"))
    assert edit(os.path.join(other, "docs", "notes.md"), cwd=root)[0] is None, "other repo's own boundary ignored"
    assert is_deny(edit(os.path.join(other, "src", "a.go"), cwd=root)[0]), "other repo's boundary not enforced"
    assert is_deny(edit(os.path.join(root, "docs", "a.md"), cwd=other)[0]), "this repo's boundary not enforced"

    unfreeze(other)
    unfreeze(root)


def row_6_no_jq(root, parent):
    """jq absent: allow plus warning, NOT deny. Deliberately unlike main-branch-guard.sh."""
    freeze(root, os.path.join(root, "src"))
    env = dict(os.environ, PATH=bin_without_jq(parent))

    result, err = edit(os.path.join(root, "docs", "notes.md"), cwd=root, env=env)
    assert result is None, "denied when jq is missing (fail-closed regression)"
    assert "jq" in err, f"no jq warning: {err!r}"
    assert len(err.strip().splitlines()) == 1, f"jq warning is not one line: {err!r}"

    unfreeze(root)


def main():
    parent = tempfile.mkdtemp(prefix="freeze-test-")
    try:
        root = make_repo(parent, "repo")
        other = make_repo(parent, "other")
        row_1_inside_boundary(root)
        row_2_outside_boundary(root)
        row_3_no_boundary(root)
        row_4_unparseable_path(root)
        row_5_different_repo(root, other)
        row_6_no_jq(root, parent)
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    print("PASS  freeze-guard (matrix rows 1-6)")


if __name__ == "__main__":
    main()
