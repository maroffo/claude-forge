#!/usr/bin/env python3
# ABOUTME: Tests for context-watcher.py, band nudges from transcript token usage
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_context_watcher.py

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

HOOK = os.path.join(os.path.dirname(__file__), "..", "context-watcher.py")
WINDOW = 100_000  # round window so token counts map to percentages directly
# Pin the compact threshold so bands are deterministic regardless of the
# ambient CLAUDE_AUTOCOMPACT_PCT_OVERRIDE. Offsets (15, 8, 3) -> bands 65/72/77.
THRESHOLD = 80


def marker_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return os.path.join(
        os.path.expanduser("~"), ".claude", "tmp", f"context-watcher-{safe}"
    )


def write_transcript(tokens):
    """Transcript whose last assistant record totals `tokens` context tokens."""
    fh = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    )
    fh.write(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
    fh.write("not json at all\n")
    fh.write(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "usage": {
                        "input_tokens": 2,
                        "cache_creation_input_tokens": tokens // 2,
                        "cache_read_input_tokens": tokens - tokens // 2 - 2,
                        "output_tokens": 999,
                    }
                },
            }
        )
        + "\n"
    )
    fh.close()
    return fh.name


def run_hook(payload, extra_env=None):
    env = dict(
        os.environ,
        CONTEXT_WATCHER_WINDOW=str(WINDOW),
        CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=str(THRESHOLD),
    )
    if extra_env is not None:
        env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload),
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def cleanup(session_id, transcript=None):
    for path in (marker_path(session_id), transcript):
        if path and os.path.exists(path):
            os.unlink(path)


def payload(sid, transcript):
    return {
        "hook_event_name": "PostToolUse",
        "session_id": sid,
        "transcript_path": transcript,
    }


def nudge_context(out):
    data = json.loads(out)
    return data["hookSpecificOutput"]["additionalContext"]


def test_below_threshold_silent():
    sid = f"test-{uuid.uuid4()}"
    transcript = write_transcript(50_000)  # 50% < lowest band (65)
    out = run_hook(payload(sid, transcript))
    assert out == "", out
    assert not os.path.exists(marker_path(sid))
    cleanup(sid, transcript)
    print("PASS  below lowest band stays silent")


def test_first_band_nudges_once():
    sid = f"test-{uuid.uuid4()}"
    transcript = write_transcript(65_000)  # 65% -> band 65 (threshold 80 - 15)
    out = run_hook(payload(sid, transcript))
    ctx = nudge_context(out)
    assert "[context-watcher]" in ctx and "65%" in ctx, ctx
    assert "80%" in ctx, ctx  # names the auto-compact threshold
    assert "quality_reports/plans/active/" in ctx, ctx
    # same band again: silent
    out2 = run_hook(payload(sid, transcript))
    assert out2 == "", out2
    cleanup(sid, transcript)
    print("PASS  first band nudges exactly once")


def test_band_escalation():
    sid = f"test-{uuid.uuid4()}"
    t65 = write_transcript(65_000)  # band 65
    t73 = write_transcript(73_000)  # band 72
    t78 = write_transcript(78_000)  # band 77
    assert nudge_context(run_hook(payload(sid, t65)))
    assert "73%" in nudge_context(run_hook(payload(sid, t73)))
    assert "78%" in nudge_context(run_hook(payload(sid, t78)))
    assert run_hook(payload(sid, t78)) == ""
    cleanup(sid, t65)
    cleanup(sid, t73)
    cleanup(sid, t78)
    print("PASS  bands escalate 65 -> 72 -> 77, once each")


def test_post_compact_drop_rearms():
    sid = f"test-{uuid.uuid4()}"
    t65 = write_transcript(65_000)
    t10 = write_transcript(10_000)
    assert nudge_context(run_hook(payload(sid, t65)))
    assert run_hook(payload(sid, t10)) == ""  # drop clears the marker
    assert not os.path.exists(marker_path(sid))
    assert nudge_context(run_hook(payload(sid, t65)))  # climbs again -> nudges again
    cleanup(sid, t65)
    cleanup(sid, t10)
    print("PASS  post-compact drop rearms the watcher")


def test_window_autodetect_1m_default():
    """No window override: 1M is assumed unless disabled, so 250K reads ~25% (silent);
    disabling 1M drops the window to 200K and the same tokens exceed the top band."""
    sid = f"test-{uuid.uuid4()}"
    transcript = write_transcript(250_000)
    # 1M default: 25% < lowest band -> silent.
    out = run_hook(payload(sid, transcript),
                   extra_env={"CONTEXT_WATCHER_WINDOW": "", "CLAUDE_CODE_DISABLE_1M_CONTEXT": "0"})
    assert out == "", out
    # 1M disabled -> 200K window: 125% -> tops out, nudges.
    out2 = run_hook(payload(sid, transcript),
                    extra_env={"CONTEXT_WATCHER_WINDOW": "", "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"})
    assert "[context-watcher]" in nudge_context(out2), out2
    cleanup(sid, transcript)
    print("PASS  window auto-detects 1M vs 200K from DISABLE_1M_CONTEXT")


def test_large_trailing_record_still_found():
    """A multi-MB tool result after the assistant record must not blind the watcher."""
    sid = f"test-{uuid.uuid4()}"
    transcript = write_transcript(65_000)
    with open(transcript, "a", encoding="utf-8") as fh:
        junk = json.dumps({"type": "user", "message": {"content": "x" * 500_000}})
        fh.write(junk + "\n")  # ~500KB line, larger than the first 256KB span
    out = run_hook(payload(sid, transcript))
    assert "65%" in nudge_context(out), out
    cleanup(sid, transcript)
    print("PASS  assistant record found past a large trailing tool result")


def test_missing_transcript_fails_open():
    sid = f"test-{uuid.uuid4()}"
    out = run_hook(payload(sid, "/nonexistent/transcript.jsonl"))
    assert out == "", out
    out = run_hook({"hook_event_name": "PostToolUse", "session_id": sid})
    assert out == "", out
    cleanup(sid)
    print("PASS  missing transcript fails open")


def main():
    test_below_threshold_silent()
    test_first_band_nudges_once()
    test_band_escalation()
    test_post_compact_drop_rearms()
    test_window_autodetect_1m_default()
    test_large_trailing_record_still_found()
    test_missing_transcript_fails_open()
    print("test_context_watcher: all tests passed")


if __name__ == "__main__":
    main()
