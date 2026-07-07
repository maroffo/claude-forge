#!/usr/bin/env python3
# ABOUTME: Dual-event hook nudging /learning-docs at deliberate session boundaries
# ABOUTME: PreCompact(manual) stashes a marker; SessionStart(compact|clear) prints the nudge

"""Retrospective nudge at deliberate context boundaries.

Long-running sessions (days) rarely reach SessionEnd, so retrospectives never
get prompted. The deliberate boundaries are manual /compact and /clear; this
hook nudges /learning-docs exactly there and nowhere else:

- PreCompact with trigger=manual writes a marker file (PreCompact stdout is
  not injected into context, so the nudge itself cannot happen here).
- SessionStart with source=compact prints the nudge only if the marker exists
  (manual compact), then consumes it. Auto-compacts fire mid-task: nudging
  there would derail work, so they stay silent.
- SessionStart with source=clear always nudges: /clear is an end-of-thread
  signal and learning-docs reads session files and git, not chat context.

Fail-open: any error exits 0 silently.
"""

import json
import os
import re
import sys
from pathlib import Path

COMPACT_NUDGE = (
    "[retrospective-nudge] Manual /compact: a work phase likely just closed. "
    "Consider running /learning-docs to capture the retrospective while the "
    "session files are fresh (traces are snapshotted automatically)."
)
CLEAR_NUDGE = (
    "[retrospective-nudge] Fresh context after /clear. If the previous thread "
    "shipped significant work without a retrospective, run /learning-docs: it "
    "reads session files and git history, not chat context."
)


def _marker(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return Path.home() / ".claude" / "tmp" / f"retro-nudge-{safe}"


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    event = payload.get("hook_event_name", "")
    session_id = payload.get("session_id") or "unknown"

    if event == "PreCompact":
        if payload.get("trigger") == "manual":
            marker = _marker(session_id)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()
        return

    if event == "SessionStart":
        source = payload.get("source", "")
        if source == "clear":
            print(CLEAR_NUDGE)
        elif source == "compact":
            marker = _marker(session_id)
            if marker.exists():
                marker.unlink()
                print(COMPACT_NUDGE)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open: a broken nudge must never break a session
    sys.exit(0)
