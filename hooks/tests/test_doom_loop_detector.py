#!/usr/bin/env python3
# ABOUTME: Tests for doom-loop-detector.py — repeated invocations against a temp session state
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_doom_loop_detector.py

import json
import os
import re
import subprocess
import sys
import uuid

HOOK = os.path.join(os.path.dirname(__file__), "..", "doom-loop-detector.py")


def sanitized_state_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return os.path.join(
        os.path.expanduser("~"), ".claude", "tmp", "claude-doom-loop-{}.json".format(safe)
    )


def run_hook(session_id, tool_name="Edit", file_path="/repo/app/main.py"):
    payload = json.dumps({
        "hook_event_name": "PostToolUse",
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
    })
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def cleanup(session_id):
    path = sanitized_state_path(session_id)
    if os.path.exists(path):
        os.unlink(path)


def main():
    sid = "test-{}".format(uuid.uuid4().hex[:12])
    try:
        # Edits 1-4: silent
        for i in range(4):
            assert run_hook(sid) is None, "edit {} should be silent".format(i + 1)
        # Edit 5: nudge
        out = run_hook(sid)
        assert out and "edit #5" in out["hookSpecificOutput"]["additionalContext"], out
        # Edits 6-7: silent again
        assert run_hook(sid) is None, "edit 6 should be silent"
        assert run_hook(sid) is None, "edit 7 should be silent"
        # Edit 8: re-nudge
        out = run_hook(sid)
        assert out and "edit #8" in out["hookSpecificOutput"]["additionalContext"], out
        # A different file has its own counter
        assert run_hook(sid, file_path="/repo/other.py") is None, "other file starts fresh"
        # Write and MultiEdit share the counter with Edit: edits 9, 10 silent, 11 nudges
        assert run_hook(sid, tool_name="Write") is None, "edit 9 should be silent"
        assert run_hook(sid, tool_name="MultiEdit") is None, "edit 10 should be silent"
        out = run_hook(sid, tool_name="Write")
        assert out and "edit #11" in out["hookSpecificOutput"]["additionalContext"], out
        # Non-edit tools are ignored
        assert run_hook(sid, tool_name="Bash") is None, "non-edit tool ignored"
        # Missing file_path tolerated
        payload = json.dumps({"tool_name": "Edit", "tool_input": {}, "session_id": sid})
        proc = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0 and not proc.stdout.strip(), "missing file_path"
        # Tampered state (non-int counts) must not crash and must reset cleanly
        with open(sanitized_state_path(sid), "w", encoding="utf-8") as fh:
            json.dump({"/repo/app/main.py": "eleven", "/x.py": -3}, fh)
        assert run_hook(sid) is None, "tampered state tolerated (counter resets to 1)"
        # Non-dict state JSON tolerated
        with open(sanitized_state_path(sid), "w", encoding="utf-8") as fh:
            fh.write("[1,2,3]")
        assert run_hook(sid) is None, "non-dict state tolerated"
    finally:
        cleanup(sid)

    # Hostile session id: no crash, and state lands at the sanitized in-dir path
    hostile = "../../etc/passwd"
    try:
        assert run_hook(hostile) is None
        assert os.path.exists(sanitized_state_path(hostile)), "state must land at the sanitized path"
    finally:
        cleanup(hostile)

    # Malformed stdin tolerated
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip(), "malformed stdin"

    print("PASS  doom-loop-detector (14 cases)")


if __name__ == "__main__":
    main()
