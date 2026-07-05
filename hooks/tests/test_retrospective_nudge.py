#!/usr/bin/env python3
# ABOUTME: Tests for retrospective-nudge.py, learning-docs nudge on manual compact and clear
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_retrospective_nudge.py

import json
import os
import re
import subprocess
import sys
import uuid

HOOK = os.path.join(os.path.dirname(__file__), "..", "retrospective-nudge.py")


def marker_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return os.path.join(
        os.path.expanduser("~"), ".claude", "tmp", f"retro-nudge-{safe}"
    )


def run_hook(payload):
    proc = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload),
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def cleanup(session_id):
    path = marker_path(session_id)
    if os.path.exists(path):
        os.unlink(path)


def test_manual_precompact_writes_marker():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook({"hook_event_name": "PreCompact", "session_id": sid, "trigger": "manual"})
    assert out == "", out  # PreCompact stdout is not injected: stay silent
    assert os.path.exists(marker_path(sid))
    cleanup(sid)
    print("PASS  manual PreCompact writes marker")


def test_auto_precompact_writes_no_marker():
    sid = f"test-{uuid.uuid4()}"
    run_hook({"hook_event_name": "PreCompact", "session_id": sid, "trigger": "auto"})
    assert not os.path.exists(marker_path(sid))
    print("PASS  auto PreCompact writes no marker")


def test_sessionstart_compact_with_marker_nudges_once():
    sid = f"test-{uuid.uuid4()}"
    run_hook({"hook_event_name": "PreCompact", "session_id": sid, "trigger": "manual"})
    out = run_hook({"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"})
    assert "/learning-docs" in out, out
    assert not os.path.exists(marker_path(sid)), "marker must be consumed"
    out2 = run_hook({"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"})
    assert out2 == "", out2
    print("PASS  compact with marker nudges once, consumes marker")


def test_sessionstart_compact_without_marker_is_silent():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook({"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"})
    assert out == "", out
    print("PASS  compact without marker (auto-compact) -> silent")


def test_sessionstart_clear_always_nudges():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook({"hook_event_name": "SessionStart", "session_id": sid, "source": "clear"})
    assert "/learning-docs" in out, out
    print("PASS  clear -> nudge")


def test_sessionstart_startup_is_silent():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook({"hook_event_name": "SessionStart", "session_id": sid, "source": "startup"})
    assert out == "", out
    print("PASS  startup -> silent")


if __name__ == "__main__":
    test_manual_precompact_writes_marker()
    test_auto_precompact_writes_no_marker()
    test_sessionstart_compact_with_marker_nudges_once()
    test_sessionstart_compact_without_marker_is_silent()
    test_sessionstart_clear_always_nudges()
    test_sessionstart_startup_is_silent()
    print("PASS  retrospective-nudge (6 cases)")
