#!/usr/bin/env python3
# ABOUTME: PostToolUse watcher that estimates context usage from the transcript tail
# ABOUTME: Nudges saving resume state at 60/75/85% bands before auto-compact fires

"""Context-occupancy watcher for the auto-compact boundary.

Auto-compact fires with no warning and its summary is lossy; the reliable
recovery channel is state on disk (living plan, .continue-here.md), but
nothing tells the model the boundary is near. Hooks receive no context-usage
fields on stdin, so this hook computes occupancy the same way the statusline
does: from the last assistant record in transcript_path,
input_tokens + cache_creation_input_tokens + cache_read_input_tokens.

At 60/75/85% of the compaction window it injects one nudge per band (via
PostToolUse hookSpecificOutput.additionalContext) telling the model to save
resume state now. A per-session marker file remembers the last band emitted;
a drop back below the lowest band (post-compact) resets it so the next climb
nudges again.

Window size is not discoverable from hook input: CONTEXT_WATCHER_WINDOW or
CLAUDE_CODE_AUTO_COMPACT_WINDOW (absolute tokens) override the 200K default.

Fail-open: any error exits 0 with no output.
"""

import json
import os
import re
import sys
from pathlib import Path

BANDS = (60, 75, 85)
DEFAULT_WINDOW = 200_000
TAIL_BYTES = 262_144
MAX_SCAN_BYTES = 16_777_216  # single tool results can exceed 2MB; cap the backward scan

NUDGE = (
    "[context-watcher] Context is at ~{pct}% of the compaction window "
    "(~{tokens} tokens of {window}). Auto-compact can fire without warning "
    "and its summary is lossy. Save resume state now: update the living "
    "plan's ## Progress and Next Action in quality_reports/plans/active/, "
    "or write .continue-here.md (see plan-first-workflow), then continue "
    "the task."
)


def _marker(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return Path.home() / ".claude" / "tmp" / f"context-watcher-{safe}"


def window_tokens() -> int:
    for var in ("CONTEXT_WATCHER_WINDOW", "CLAUDE_CODE_AUTO_COMPACT_WINDOW"):
        raw = os.environ.get(var, "")
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
    return DEFAULT_WINDOW


def context_tokens(transcript_path: str) -> int | None:
    """Token count of the newest assistant record, statusline formula.

    Scans backward in growing spans: a single trailing tool result can be
    multi-MB, pushing the last assistant record past any fixed tail, and that
    is exactly the high-occupancy moment the watcher exists for.
    """
    path = Path(transcript_path)
    size = path.stat().st_size
    span = TAIL_BYTES
    while True:
        with path.open("rb") as fh:
            fh.seek(max(0, size - span))
            tail = fh.read(span).decode("utf-8", errors="replace")
        for line in reversed(tail.splitlines()):
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if record.get("type") != "assistant" or record.get("isSidechain"):
                continue
            usage = (record.get("message") or {}).get("usage")
            if not isinstance(usage, dict):
                continue
            return (
                int(usage.get("input_tokens") or 0)
                + int(usage.get("cache_creation_input_tokens") or 0)
                + int(usage.get("cache_read_input_tokens") or 0)
            )
        if span >= size or span >= MAX_SCAN_BYTES:
            return None
        span = min(span * 4, MAX_SCAN_BYTES)


def last_band(marker: Path) -> int:
    try:
        return int(marker.read_text().strip())
    except (OSError, ValueError):
        return 0


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    transcript = payload.get("transcript_path") or ""
    session_id = payload.get("session_id") or "unknown"
    if not transcript:
        return

    tokens = context_tokens(transcript)
    if tokens is None:
        return
    window = window_tokens()
    pct = tokens * 100 // window

    marker = _marker(session_id)
    band = max((b for b in BANDS if pct >= b), default=0)

    if band == 0:
        # Post-compact drop: rearm so the next climb nudges again.
        marker.unlink(missing_ok=True)
        return
    if band <= last_band(marker):
        return

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(band))
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": NUDGE.format(
                        pct=pct, tokens=tokens, window=window
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open: a broken watcher must never break a session
    sys.exit(0)
