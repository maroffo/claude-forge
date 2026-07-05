#!/usr/bin/env python3
# ABOUTME: Tests for score-evidence-guard.py — synthetic transcripts through the real hook process
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_score_evidence_guard.py

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "score-evidence-guard.py")


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
    return {"type": "assistant", "message": {"content": [block]}}


def assistant_text(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def run_hook(lines, stop_hook_active=False):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for obj in lines:
            fh.write(obj if isinstance(obj, str) else json.dumps(obj))
            fh.write("\n")
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
    verify_ok = assistant_tool("Bash", tool_id="v1", command="make check && make test-e2e")
    verify_failed = assistant_tool("Bash", tool_id="v2", command="make check && make test-e2e")
    unrelated_bash = assistant_tool("Bash", command="git status")
    score = assistant_text("Review done.\nSCORE: 92/100 (threshold: 90, gate: pr)\nReady.")
    prose = assistant_text("Quality looks good, well above the bar.")

    # 1. SCORE with successful verify after the last edit -> allow
    expect_allow(
        run_hook([human(), edit_py, tool_result(), verify_ok, tool_result("v1"), score]),
        "score-with-fresh-evidence",
    )

    # 2. SCORE with no verify anywhere in the session -> block
    expect_block(
        run_hook([human(), edit_py, tool_result(), unrelated_bash, tool_result(), score]),
        "score-no-verify",
    )

    # 3. SCORE with verify only BEFORE the last edit (stale evidence) -> block
    expect_block(
        run_hook([human(), verify_ok, tool_result("v1"), edit_py, tool_result(), score]),
        "score-stale-evidence",
    )

    # 4. SCORE where the fresh verify FAILED (is_error) -> block
    expect_block(
        run_hook([human(), edit_py, tool_result(), verify_failed, tool_result("v2", is_error=True), score]),
        "score-failed-verify",
    )

    # 5. No SCORE line this turn -> allow (verify-before-stop owns plain edits)
    expect_allow(
        run_hook([human(), edit_py, tool_result(), prose]),
        "no-score-line",
    )

    # 6. stop_hook_active guard -> allow even without evidence
    expect_allow(
        run_hook([human(), edit_py, tool_result(), score], stop_hook_active=True),
        "stop-hook-active",
    )

    # 7. SCORE emitted in a PREVIOUS turn only -> allow
    expect_allow(
        run_hook([human(), score, human("next"), unrelated_bash, tool_result()]),
        "previous-turn-score",
    )

    # 8. SCORE with no edits at all, successful verify earlier in session -> allow
    expect_allow(
        run_hook([human(), verify_ok, tool_result("v1"), human("score it"), score]),
        "score-no-edits-verified-session",
    )

    # 9. SCORE with no edits and no verify -> block (pure fabrication case)
    expect_block(
        run_hook([human("score it"), score]),
        "score-no-edits-no-verify",
    )

    # 10. Verify on a sidechain does not count as evidence -> block
    sidechain_verify = dict(assistant_tool("Bash", tool_id="v3", command="make check"), isSidechain=True)
    expect_block(
        run_hook([human(), edit_py, tool_result(), sidechain_verify, tool_result("v3"), score]),
        "sidechain-verify-ignored",
    )

    # 11. SCORE-like text inside a non-matching line (e.g. quoting the rule) -> allow
    quoting = assistant_text("The extractor keys on the literal form `SCORE: <n>` per the rule.")
    expect_allow(
        run_hook([human(), quoting]),
        "score-mention-not-report",
    )

    # 12. Freshest evidence is red: edit -> pass -> FAIL -> SCORE -> block
    expect_block(
        run_hook([
            human(), edit_py, tool_result(),
            verify_ok, tool_result("v1"),
            verify_failed, tool_result("v2", is_error=True),
            score,
        ]),
        "latest-evidence-red",
    )

    # 13. Recovered: edit -> FAIL -> pass -> SCORE -> allow
    expect_allow(
        run_hook([
            human(), edit_py, tool_result(),
            verify_failed, tool_result("v2", is_error=True),
            verify_ok, tool_result("v1"),
            score,
        ]),
        "recovered-after-failure",
    )

    # 14. Write-class subagent launched after the verify invalidates evidence -> block
    engineer = assistant_tool("Task", tool_id="t1", subagent_type="software-engineer", prompt="fix it")
    expect_block(
        run_hook([human(), verify_ok, tool_result("v1"), engineer, tool_result("t1"), score]),
        "write-agent-after-verify",
    )

    # 15. Read-only reviewer agent after the verify does NOT invalidate -> allow
    reviewer = assistant_tool("Task", tool_id="t2", subagent_type="security-reviewer", prompt="review")
    expect_allow(
        run_hook([human(), edit_py, tool_result(), verify_ok, tool_result("v1"), reviewer, tool_result("t2"), score]),
        "reviewer-after-verify",
    )

    # 16. Verify tool_use without an id cannot be correlated -> not evidence -> block
    verify_no_id = assistant_tool("Bash", command="make check && make test-e2e")
    expect_block(
        run_hook([human(), edit_py, tool_result(), verify_no_id, tool_result(), score]),
        "idless-verify-not-evidence",
    )

    # 17. Poisoned transcript lines (deep nesting, garbage) -> fail-open, logic intact
    poison = "[" * 5000
    expect_allow(
        run_hook([human(), poison, "not json at all", edit_py, tool_result(), verify_ok, tool_result("v1"), score]),
        "poisoned-lines-fail-open",
    )

    print("test_score_evidence_guard: all tests passed")


if __name__ == "__main__":
    main()
