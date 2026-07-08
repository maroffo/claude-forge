#!/usr/bin/env python3
# ABOUTME: Tests for compact-resume.py, resume prompt after auto-compact boundaries
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_compact_resume.py

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

HOOK = os.path.join(os.path.dirname(__file__), "..", "compact-resume.py")


def marker_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return os.path.join(
        os.path.expanduser("~"), ".claude", "tmp", f"compact-resume-{safe}"
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


def test_auto_precompact_writes_marker():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook(
        {"hook_event_name": "PreCompact", "session_id": sid,
         "trigger": "auto", "cwd": "/tmp"}
    )
    assert out == "", out  # PreCompact stdout is not injected: stay silent
    assert os.path.exists(marker_path(sid))
    cleanup(sid)
    print("PASS  auto PreCompact writes marker")


def test_manual_precompact_writes_no_marker():
    sid = f"test-{uuid.uuid4()}"
    run_hook({"hook_event_name": "PreCompact", "session_id": sid, "trigger": "manual"})
    assert not os.path.exists(marker_path(sid))
    print("PASS  manual PreCompact writes no marker")


def test_sessionstart_compact_with_marker_prints_resume():
    sid = f"test-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as cwd:
        plans = os.path.join(cwd, "quality_reports", "plans", "active")
        os.makedirs(plans)
        with open(os.path.join(plans, "2026-07-08_thing.md"), "w") as fh:
            fh.write("# plan\n")
        with open(os.path.join(cwd, ".continue-here.md"), "w") as fh:
            fh.write("## Next Action\n")
        run_hook(
            {"hook_event_name": "PreCompact", "session_id": sid,
             "trigger": "auto", "cwd": cwd}
        )
        out = run_hook(
            {"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"}
        )
    assert "[compact-resume]" in out, out
    assert "quality_reports/plans/active/2026-07-08_thing.md" in out, out
    assert ".continue-here.md" in out, out
    assert not os.path.exists(marker_path(sid))  # marker consumed
    cleanup(sid)
    print("PASS  SessionStart(compact) with marker prints resume and consumes it")


def test_sessionstart_compact_without_marker_silent():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook(
        {"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"}
    )
    assert out == "", out  # manual compact: retrospective-nudge owns that boundary
    print("PASS  SessionStart(compact) without marker stays silent")


def test_sessionstart_other_sources_silent():
    sid = f"test-{uuid.uuid4()}"
    run_hook(
        {"hook_event_name": "PreCompact", "session_id": sid,
         "trigger": "auto", "cwd": "/tmp"}
    )
    for source in ("clear", "startup", "resume"):
        out = run_hook(
            {"hook_event_name": "SessionStart", "session_id": sid, "source": source}
        )
        assert out == "", (source, out)
    cleanup(sid)
    print("PASS  SessionStart clear/startup/resume stay silent")


def test_marker_cwd_without_state_files_uses_fallback():
    sid = f"test-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as cwd:
        run_hook(
            {"hook_event_name": "PreCompact", "session_id": sid,
             "trigger": "auto", "cwd": cwd}
        )
        out = run_hook(
            {"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"}
        )
    assert "[compact-resume]" in out, out
    assert "if present" in out, out  # fallback wording, no concrete files found
    cleanup(sid)
    print("PASS  cwd without state files falls back to generic pointer")


def main():
    test_auto_precompact_writes_marker()
    test_manual_precompact_writes_no_marker()
    test_sessionstart_compact_with_marker_prints_resume()
    test_sessionstart_compact_without_marker_silent()
    test_sessionstart_other_sources_silent()
    test_marker_cwd_without_state_files_uses_fallback()
    print("test_compact_resume: all tests passed")


if __name__ == "__main__":
    main()
