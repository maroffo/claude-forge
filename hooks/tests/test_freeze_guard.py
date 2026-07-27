#!/usr/bin/env python3
# ABOUTME: E2E tests for hooks/freeze-guard.sh, matrix rows 1-8 of the gstack-borrowings plan
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_freeze_guard.py

import json
import os
import shutil
import subprocess
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


def tool_payload(tool, file_path):
    """The payload shape each guarded tool really sends. NotebookEdit names its target
    `notebook_path` and has no `file_path` at all, which is the whole point of testing
    it with its own shape rather than a fabricated one."""
    if tool == "NotebookEdit":
        tool_input = {"notebook_path": file_path, "cell_id": "c1", "new_source": "x"}
    elif tool == "Write":
        tool_input = {"file_path": file_path, "content": "x"}
    else:
        tool_input = {"file_path": file_path, "old_string": "a", "new_string": "b"}
    return json.dumps({"tool_name": tool, "tool_input": tool_input})


def edit(file_path, cwd, tool="Edit", env=None):
    return run(tool_payload(tool, file_path), cwd, env=env)


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


def write_boundary(root, raw):
    """Write boundary file content verbatim, for the malformed-data cases."""
    with open(os.path.join(root, ".freeze-boundary"), "w") as fh:
        fh.write(raw)


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

    # Every guarded tool, in its own payload shape, is allowed inside.
    for tool in ("Write", "Edit", "NotebookEdit"):
        result, err = edit(os.path.join(src, "nb.ipynb"), cwd=root, tool=tool)
        assert result is None and err == "", f"{tool} blocked inside the boundary: {result} {err}"

    # The boundary directory itself counts as inside (exact-dir edge).
    result, _ = edit(src, cwd=root)
    assert result is None, "boundary dir itself denied"

    # A boundary written WITHOUT the trailing slash still matches inside...
    write_boundary(root, os.path.realpath(src) + "\n")
    result, _ = edit(os.path.join(src, "a.go"), cwd=root)
    assert result is None, "no-trailing-slash boundary denied an inside path"
    # ...and still does not swallow the sibling whose name it prefixes.
    result, _ = edit(os.path.join(root, "srcgen", "a.go"), cwd=root)
    assert is_deny(result), "srcgen/ passed as if inside src/ (missing trailing-slash guard)"

    # Horizontal whitespace around the path is editing debris, not part of it: a real
    # path with trailing spaces must not deny every edit under it (decision 19).
    write_boundary(root, "  " + os.path.realpath(src) + "/  \n")
    result, err = edit(os.path.join(src, "a.go"), cwd=root)
    assert result is None and err == "", f"padded boundary caused a false deny: {result} {err}"
    result, _ = edit(os.path.join(root, "docs", "a.md"), cwd=root)
    assert is_deny(result), "padded boundary stopped enforcing"
    assert os.path.realpath(src) + "`" in reason(result), f"padding leaked into the message: {reason(result)!r}"

    # An interior space is a legal directory name, so trimming must not touch it.
    spaced = os.path.join(root, "my src")
    os.makedirs(spaced, exist_ok=True)
    freeze(root, spaced)
    result, err = edit(os.path.join(spaced, "a.go"), cwd=root)
    assert result is None and err == "", f"boundary dir with an interior space denied: {result} {err}"

    # A boundary spelled through a symlink must not produce a false deny: the hook
    # resolves both sides physically before comparing.
    link = os.path.join(root, "src-link")
    os.symlink(src, link)
    write_boundary(root, link + "/\n")
    result, err = edit(os.path.join(src, "a.go"), cwd=root)
    assert result is None, f"symlinked boundary spelling caused a false deny: {result} {err}"


def row_2_outside_boundary(root):
    """Boundary set, mutating tool outside: deny, naming the boundary and the remedy."""
    freeze(root, os.path.join(root, "src"))
    outside = os.path.join(root, "docs", "notes.md")

    for tool in ("Write", "Edit", "NotebookEdit"):
        target = os.path.join(root, "docs", "nb.ipynb") if tool == "NotebookEdit" else outside
        result, _ = edit(target, cwd=root, tool=tool)
        assert is_deny(result), f"{tool} outside the boundary was allowed"
        msg = reason(result)
        assert os.path.realpath(os.path.join(root, "src")) in msg, f"{tool}: boundary path absent from {msg!r}"
        assert "/freeze off" in msg, f"{tool}: remedy absent from {msg!r}"
        assert ".freeze-boundary" in msg, f"{tool}: boundary file absent from {msg!r}"

    # The session cwd is irrelevant: what matters is where the edited file lives.
    result, _ = edit(outside, cwd=os.path.join(root, "src"))
    assert is_deny(result), "deny depends on the session cwd"


def row_3_no_boundary(root):
    """No boundary file: allow with zero output on stdout and stderr, before and after a lift."""
    for target in (os.path.join(root, "docs", "notes.md"), os.path.join(root, "src", "a.go")):
        result, err = edit(target, cwd=root)
        assert result is None, "denied with no boundary file"
        assert err == "", f"noise when inert: {err!r}"

    # Same after `/freeze off` removes an active boundary.
    freeze(root, os.path.join(root, "src"))
    unfreeze(root)
    result, err = edit(os.path.join(root, "docs", "notes.md"), cwd=root)
    assert result is None and err == "", f"still enforcing after the boundary was lifted: {result} {err}"


def row_4_unusable_data(root):
    """Boundary present, path or boundary garbled: ALLOW plus one line of stderr (decision 1)."""
    freeze(root, os.path.join(root, "src"))

    def assert_allowed_with_warning(payload, label):
        result, err = run(payload, cwd=root)
        assert result is None, f"{label}: denied instead of failing open"
        assert err.strip(), f"{label}: no warning printed"
        assert len(err.strip().splitlines()) == 1, f"{label}: warning is not one line: {err!r}"
        assert "freeze-guard:" in err, f"{label}: warning is unattributed: {err!r}"

    assert_allowed_with_warning("not json at all {", "garbled JSON")
    assert_allowed_with_warning(json.dumps({"tool_name": "Edit", "tool_input": {}}), "missing file_path")
    assert_allowed_with_warning(tool_payload("Edit", ""), "empty file_path")
    assert_allowed_with_warning(
        json.dumps({"tool_name": "NotebookEdit", "tool_input": {"cell_id": "c1", "new_source": "x"}}),
        "missing notebook_path",
    )
    assert_allowed_with_warning(
        tool_payload("Edit", os.path.join(root, "docs", "a\nb.md")),
        "newline in file_path",
    )

    # Unusable boundary data is the same class: nothing to enforce, so allow and say so.
    outside = tool_payload("Edit", os.path.join(root, "docs", "a.md"))
    write_boundary(root, "\n")
    assert_allowed_with_warning(outside, "empty boundary file")
    write_boundary(root, "   \t  \n")
    assert_allowed_with_warning(outside, "whitespace-only boundary file")

    # Outside any git repo there is no boundary to consult: silent allow, no warning.
    with tempfile.TemporaryDirectory() as bare:
        result, err = run("not json at all {", cwd=bare)
        assert result is None and err == "", f"warned with no repo in sight: {err!r}"


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


def row_6_no_jq(root, parent):
    """jq absent: allow plus warning, NOT deny. Deliberately unlike main-branch-guard.sh."""
    freeze(root, os.path.join(root, "src"))
    env = dict(os.environ, PATH=bin_without_jq(parent))

    result, err = edit(os.path.join(root, "docs", "notes.md"), cwd=root, env=env)
    assert result is None, "denied when jq is missing (fail-closed regression)"
    assert "jq" in err, f"no jq warning: {err!r}"
    assert len(err.strip().splitlines()) == 1, f"jq warning is not one line: {err!r}"


def row_7_relative_path(root):
    """A relative file_path is resolved against the hook's cwd, then judged like any other."""
    freeze(root, os.path.join(root, "src"))

    result, err = edit(os.path.join("src", "a.go"), cwd=root)
    assert result is None and err == "", f"relative in-boundary path blocked: {result} {err}"

    result, _ = edit(os.path.join("docs", "notes.md"), cwd=root)
    assert is_deny(result), "relative out-of-boundary path allowed"
    assert os.path.realpath(os.path.join(root, "docs", "notes.md")) in reason(result), \
        f"relative path not resolved in the message: {reason(result)!r}"

    # Resolution is relative to the process cwd, not to the repo root.
    result, _ = edit(os.path.join("deep", "nested.go"), cwd=os.path.join(root, "src"))
    assert result is None, "relative path resolved against the repo root instead of the cwd"


def row_8_foreign_boundary(root, elsewhere):
    """A boundary resolving outside the frozen repo denies every file in that repo, by design:
    freeze means only edits under <dir> are allowed here, and a foreign boundary is still an
    explicit freeze. `/freeze <dir>` refuses to write one; a hand-edited file can still hold it."""
    freeze(root, elsewhere)

    for target in ("src/a.go", "docs/notes.md", ".freeze-boundary"):
        result, _ = edit(os.path.join(root, target), cwd=root)
        assert is_deny(result), f"foreign boundary silently stopped enforcing for {target}"

    # And it does not reach into the repo it points at (the guard is repo-local).
    result, err = edit(os.path.join(elsewhere, "a.go"), cwd=root)
    assert result is None and err == "", f"foreign boundary enforced outside its own repo: {result} {err}"


def main():
    parent = tempfile.mkdtemp(prefix="freeze-test-")
    try:
        # One fresh repo per row: no row inherits another's boundary file, symlinks or
        # ordering, so a failure names its own row instead of poisoning the next.
        row_1_inside_boundary(make_repo(parent, "row1"))
        row_2_outside_boundary(make_repo(parent, "row2"))
        row_3_no_boundary(make_repo(parent, "row3"))
        row_4_unusable_data(make_repo(parent, "row4"))
        row_5_different_repo(make_repo(parent, "row5"), make_repo(parent, "row5-other"))
        row_6_no_jq(make_repo(parent, "row6"), parent)
        row_7_relative_path(make_repo(parent, "row7"))
        elsewhere = os.path.join(make_repo(parent, "row8-elsewhere"), "src")
        row_8_foreign_boundary(make_repo(parent, "row8"), elsewhere)
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    print("PASS  freeze-guard (matrix rows 1-8)")


if __name__ == "__main__":
    main()
