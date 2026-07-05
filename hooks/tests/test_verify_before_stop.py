#!/usr/bin/env python3
# ABOUTME: Tests for verify-before-stop.py — synthetic transcripts through the real hook process
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_verify_before_stop.py

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "verify-before-stop.py")


def human(text="do the thing"):
    return {"type": "user", "message": {"content": text}}


def tool_result(tool_use_id=None, is_error=False):
    block = {"type": "tool_result", "content": "ok"}
    if tool_use_id:
        block["tool_use_id"] = tool_use_id
    if is_error:
        block["is_error"] = True
    return {"type": "user", "message": {"content": [block]}}


def assistant_tool(name, tool_id=None, **tool_input):
    block = {"type": "tool_use", "name": name, "input": tool_input}
    if tool_id:
        block["id"] = tool_id
    return {
        "type": "assistant",
        "message": {"content": [block]},
    }


def run_hook(lines, stop_hook_active=False):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for obj in lines:
            fh.write(json.dumps(obj) + "\n")
        path = fh.name
    payload = json.dumps(
        {"hook_event_name": "Stop", "transcript_path": path, "stop_hook_active": stop_hook_active}
    )
    try:
        proc = subprocess.run(
            [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30
        )
    finally:
        os.unlink(path)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def expect_block(result, label):
    assert result is not None and result.get("decision") == "block", f"{label}: expected block, got {result}"


def expect_allow(result, label):
    assert result is None, f"{label}: expected allow, got {result}"


def main():
    edit_py = assistant_tool("Edit", file_path="/repo/app/main.py", old_string="a", new_string="b")
    write_md = assistant_tool("Write", file_path="/repo/README.md", content="x")
    check_run = assistant_tool("Bash", tool_id="c1", command="make check && make test-e2e")
    unrelated_bash = assistant_tool("Bash", command="git status")

    # 1. Source edit, no check after -> block
    expect_block(run_hook([human(), edit_py, tool_result(), unrelated_bash, tool_result()]), "edit-no-check")

    # 2. Source edit, then check -> allow
    expect_allow(run_hook([human(), edit_py, tool_result(), check_run, tool_result()]), "edit-then-check")

    # 3. Check BEFORE the edit only -> block
    expect_block(run_hook([human(), check_run, tool_result(), edit_py, tool_result()]), "check-before-edit")

    # 4. Docs-only turn -> allow
    expect_allow(run_hook([human(), write_md, tool_result()]), "docs-only")

    # 5. stop_hook_active guard -> allow even with unverified edits
    expect_allow(run_hook([human(), edit_py, tool_result()], stop_hook_active=True), "stop-hook-active")

    # 6. Edit belongs to a PREVIOUS turn -> allow
    expect_allow(run_hook([human(), edit_py, tool_result(), human("next question"), unrelated_bash, tool_result()]), "previous-turn-edit")

    # 7. Sidechain edits ignored -> allow
    side = dict(assistant_tool("Edit", file_path="/repo/x.go", old_string="a", new_string="b"), isSidechain=True)
    expect_allow(run_hook([human(), side, tool_result()]), "sidechain")

    # 8. Exempt paths (scratchpad/tmp) -> allow
    tmp_edit = assistant_tool("Write", file_path="/tmp/scratch/x.py", content="x")
    expect_allow(run_hook([human(), tmp_edit, tool_result()]), "exempt-path")

    # 9. Malformed lines tolerated, still blocks on the valid edit
    lines = [human(), edit_py, tool_result()]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        fh.write("not json\n")
        for obj in lines:
            fh.write(json.dumps(obj) + "\n")
        path = fh.name
    payload = json.dumps({"hook_event_name": "Stop", "transcript_path": path, "stop_hook_active": False})
    proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30)
    os.unlink(path)
    assert proc.returncode == 0, proc.stderr
    expect_block(json.loads(proc.stdout.strip()), "malformed-lines")

    # 10. Missing transcript -> allow, no crash
    payload = json.dumps({"hook_event_name": "Stop", "transcript_path": "/nonexistent/t.jsonl", "stop_hook_active": False})
    proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip(), "missing-transcript"

    # 11. NotebookEdit on .ipynb: allowed (notebooks are excluded by extension policy)
    nb = assistant_tool("NotebookEdit", notebook_path="/repo/analysis.ipynb")
    expect_allow(run_hook([human(), nb, tool_result()]), "notebook-ext-policy")

    # 12. Language-specific verify commands satisfy the gate
    for cmd in (
        "go test ./...",
        "uv run pytest -q",
        "npx tsc --noEmit",
        "cargo clippy",
        "git commit -m 'feat: x'",  # pre-commit-gate runs make check on commit
        "uv run --no-project python3 hooks/tests/test_verify_before_stop.py",
    ):
        verify = assistant_tool("Bash", tool_id="v1", command=cmd)
        expect_allow(run_hook([human(), edit_py, tool_result(), verify, tool_result()]), f"verify-cmd:{cmd}")

    # 13. Sidechain USER lines must not advance the turn boundary (regression)
    side_user = dict(human("subagent prompt"), isSidechain=True)
    expect_block(run_hook([human(), edit_py, tool_result(), side_user, tool_result()]), "sidechain-user-boundary")

    # 14. Mentioning a verify tool without running it does not satisfy the gate
    for cmd in ("echo 'run tsc later'", "grep pytest Makefile", "cat jest.config.js"):
        mention = assistant_tool("Bash", command=cmd)
        expect_block(run_hook([human(), edit_py, tool_result(), mention, tool_result()]), f"mention-only:{cmd}")

    # 15. User entry with empty content list is not a turn boundary
    empty_user = {"type": "user", "message": {"content": []}}
    expect_block(run_hook([human(), edit_py, tool_result(), empty_user]), "empty-content-user")

    # 16. Smoke: the .sh wrapper (the artifact actually registered) blocks too
    wrapper = os.path.join(os.path.dirname(__file__), "..", "verify-before-stop.sh")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for obj in (human(), edit_py, tool_result()):
            fh.write(json.dumps(obj) + "\n")
        path = fh.name
    payload = json.dumps({"hook_event_name": "Stop", "transcript_path": path, "stop_hook_active": False})
    proc = subprocess.run(["bash", wrapper], input=payload, capture_output=True, text=True, timeout=60)
    os.unlink(path)
    assert proc.returncode == 0, proc.stderr
    expect_block(json.loads(proc.stdout.strip()), "sh-wrapper")

    # 17. Check after the edit FAILED (is_error) -> not evidence -> block
    check_failed = assistant_tool("Bash", tool_id="c2", command="make check && make test-e2e")
    expect_block(
        run_hook([human(), edit_py, tool_result(), check_failed, tool_result("c2", is_error=True)]),
        "failed-check-not-evidence",
    )

    # 18. Recovered: edit -> FAIL -> pass -> allow
    expect_allow(
        run_hook([
            human(), edit_py, tool_result(),
            check_failed, tool_result("c2", is_error=True),
            check_run, tool_result("c1"),
        ]),
        "recovered-after-failure",
    )

    # 19. Freshest evidence is red: edit -> pass -> FAIL -> block
    expect_block(
        run_hook([
            human(), edit_py, tool_result(),
            check_run, tool_result("c1"),
            check_failed, tool_result("c2", is_error=True),
        ]),
        "latest-evidence-red",
    )

    # 20. Check without a tool_use id cannot be correlated -> not evidence -> block
    check_no_id = assistant_tool("Bash", command="make check && make test-e2e")
    expect_block(
        run_hook([human(), edit_py, tool_result(), check_no_id, tool_result()]),
        "idless-check-not-evidence",
    )

    print("PASS  verify-before-stop (20 cases)")


if __name__ == "__main__":
    main()
