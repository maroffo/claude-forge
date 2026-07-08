#!/usr/bin/env python3
# ABOUTME: Dual-event hook restoring task continuity across auto-compact boundaries
# ABOUTME: PreCompact(auto) stashes a marker; SessionStart(compact) injects the resume prompt

"""Resume prompt after an auto-compact truncates a session mid-task.

Auto-compact fires mid-work and replaces history with a lossy summary; the
model then tends to re-plan from the summary instead of re-anchoring on the
state files the rules already require (living plan, .continue-here.md).
The compact summarization prompt is not customizable and PreCompact stdout
is not injected into context, so the fix is a marker dance mirroring
retrospective-nudge:

- PreCompact with trigger=auto writes a marker holding the session cwd.
- SessionStart with source=compact consumes the marker and prints the resume
  prompt (SessionStart stdout IS injected), listing the concrete state files
  found in the cwd so re-anchoring is one Read away. Manual compacts skip
  this: retrospective-nudge owns that boundary.

Fail-open: any error exits 0 silently.
"""

import json
import os
import re
import sys
from pathlib import Path

RESUME = (
    "[compact-resume] This session was auto-compacted mid-task; the summary "
    "above is lossy. Re-anchor from files before continuing: read {files}, "
    "check TaskList for in_progress items, then resume the interrupted task. "
    "Trust files and git state over the summary; do not re-plan from scratch."
)
FALLBACK_FILES = (
    "the living plan in quality_reports/plans/active/ and .continue-here.md "
    "if present"
)


def _marker(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return Path.home() / ".claude" / "tmp" / f"compact-resume-{safe}"


PLAN_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}_[A-Za-z0-9._-]+\.md$")


def state_files(cwd: str) -> str:
    """Comma-separated resume files that actually exist under cwd.

    Filenames are interpolated into injected context, so only plan names
    matching the repo convention pass; anything else falls back to the
    generic pointer instead of becoming instruction text.
    """
    base = Path(cwd) if cwd else None
    if base is None or not base.is_dir():
        return FALLBACK_FILES
    found = sorted(
        str(p.relative_to(base))
        for p in base.glob("quality_reports/plans/active/*.md")
        if PLAN_NAME.match(p.name)
    )
    continue_here = base / ".continue-here.md"
    if continue_here.is_file():
        found.append(".continue-here.md")
    return ", ".join(found) if found else FALLBACK_FILES


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    event = payload.get("hook_event_name", "")
    session_id = payload.get("session_id") or "unknown"

    if event == "PreCompact":
        if payload.get("trigger") == "auto":
            marker = _marker(session_id)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(payload.get("cwd") or "")
        return

    if event == "SessionStart" and payload.get("source") == "compact":
        marker = _marker(session_id)
        if not marker.exists():
            return
        cwd = marker.read_text().strip() or payload.get("cwd") or os.getcwd()
        marker.unlink(missing_ok=True)
        print(RESUME.format(files=state_files(cwd)))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open: a broken resume prompt must never break a session
    sys.exit(0)
