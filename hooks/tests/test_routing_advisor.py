#!/usr/bin/env python3
# ABOUTME: Tests for routing-advisor.py — route matching, per-session dedup, state hygiene
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_routing_advisor.py

import json
import os
import re
import subprocess
import sys
import uuid

HOOK = os.path.join(os.path.dirname(__file__), "..", "routing-advisor.py")
STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "tmp")


def state_file(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return os.path.join(STATE_DIR, "routing-{}.json".format(safe))


def run_hook(session_id, tool_name="Edit", **tool_input):
    payload = json.dumps({
        "session_id": session_id, "tool_name": tool_name, "tool_input": tool_input,
    })
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def cleanup(session_id):
    p = state_file(session_id)
    if os.path.exists(p):
        os.unlink(p)


def ctx(result):
    return result["hookSpecificOutput"]["additionalContext"] if result else ""


def main():
    sid = "route-{}".format(uuid.uuid4().hex[:12])
    try:
        # First .py edit advises architecture + security
        out = run_hook(sid, file_path="/repo/app/main.py")
        assert "architecture-reviewer" in ctx(out) and "security-reviewer" in ctx(out), out
        # Second edit of same class: deduped, silent
        assert run_hook(sid, file_path="/repo/app/other.py") is None, "dedup failed"
        # New route class still advises (dependency on package.json)
        out = run_hook(sid, tool_name="Write", file_path="/repo/package.json")
        assert "dependency-reviewer" in ctx(out), out
        # Launching a reviewer via Agent marks it advised without output
        assert run_hook(sid, tool_name="Agent", subagent_type="database-reviewer") is None
        # ...so a later migrations edit does not re-advise database-reviewer
        out = run_hook(sid, file_path="/repo/migrations/001_init.sql")
        assert out is None or "database-reviewer" not in ctx(out), out
        # Non-edit tools ignored
        assert run_hook(sid, tool_name="Bash", command="ls") is None
    finally:
        cleanup(sid)

    # Hostile session id: state lands at the sanitized in-dir path, no traversal
    hostile = "../../etc/cron.d/evil"
    try:
        run_hook(hostile, file_path="/repo/x.md")
        assert os.path.exists(state_file(hostile)), "state must land at sanitized path"
    finally:
        cleanup(hostile)

    # Malformed stdin tolerated
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and not proc.stdout.strip()

    print("PASS  routing-advisor (8 cases)")


if __name__ == "__main__":
    main()
