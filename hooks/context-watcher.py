#!/usr/bin/env python3
# ABOUTME: PostToolUse watcher that estimates context usage from the transcript tail
# ABOUTME: Nudges saving resume state on bands just below the auto-compact threshold

"""Context-occupancy watcher for the auto-compact boundary.

Auto-compact fires with no warning and its summary is lossy; the reliable
recovery channel is state on disk (living plan, .continue-here.md), but
nothing tells the model the boundary is near. Hooks receive no context-usage
fields on stdin, so this hook computes occupancy the same way the statusline
does: from the last assistant record in transcript_path,
input_tokens + cache_creation_input_tokens + cache_read_input_tokens.

Two things must line up with the real session for the nudge to be useful:

- **Window size.** Not discoverable from hook input. The 1M context window is
  active unless CLAUDE_CODE_DISABLE_1M_CONTEXT=1, so that is the default;
  CONTEXT_WATCHER_WINDOW or CLAUDE_CODE_AUTO_COMPACT_WINDOW (absolute tokens)
  pin it explicitly. A 200K assumption on a 1M session fired the bands ~5x too
  early (the bug this replaces).
- **Threshold.** Auto-compact fires near CLAUDE_AUTOCOMPACT_PCT_OVERRIDE percent
  of the window (default AUTOCOMPACT_DEFAULT_PCT). The bands sit a few points
  BELOW that, so the nudge always precedes compaction wherever the threshold is
  set, instead of at fixed absolute percentages.

It injects one nudge per band (via PostToolUse
hookSpecificOutput.additionalContext). A per-session marker file remembers the
last band emitted; a drop back below the lowest band (post-compact) resets it
so the next climb nudges again.

Fail-open: any error exits 0 with no output.
"""

import json
import os
import re
import sys
from pathlib import Path

WINDOW_1M = 1_000_000
WINDOW_STANDARD = 200_000
# Auto-compact's default trigger, as a percent of the window, when
# CLAUDE_AUTOCOMPACT_PCT_OVERRIDE is unset.
AUTOCOMPACT_DEFAULT_PCT = 92
# Pre-warning bands sit these many percentage points below the compact
# threshold, ascending toward it, so the nudge always precedes auto-compact.
BAND_OFFSETS = (15, 8, 3)
TAIL_BYTES = 262_144
MAX_SCAN_BYTES = 16_777_216  # single tool results can exceed 2MB; cap the backward scan

NUDGE = (
    "[context-watcher] Context is at ~{pct}% of the {window}-token window "
    "(~{tokens} tokens); auto-compact fires near {threshold}%. Its summary is "
    "lossy, so save resume state now: update the living plan's ## Progress and "
    "Next Action in quality_reports/plans/active/, or write .continue-here.md "
    "(see plan-first-workflow), then continue the task."
)


def _marker(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return Path.home() / ".claude" / "tmp" / f"context-watcher-{safe}"


def window_tokens() -> int:
    """Real context window in tokens.

    An explicit override wins; otherwise the 1M window is assumed active unless
    it was explicitly disabled. Guessing 200K on a 1M session is the failure
    this replaces, so the default leans large; a genuinely 200K deployment sets
    CLAUDE_CODE_DISABLE_1M_CONTEXT=1 or pins CONTEXT_WATCHER_WINDOW.
    """
    for var in ("CONTEXT_WATCHER_WINDOW", "CLAUDE_CODE_AUTO_COMPACT_WINDOW"):
        raw = os.environ.get(var, "").strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
    if os.environ.get("CLAUDE_CODE_DISABLE_1M_CONTEXT", "").strip() == "1":
        return WINDOW_STANDARD
    return WINDOW_1M


def autocompact_pct() -> int:
    """Percent of the window at which auto-compact fires."""
    raw = os.environ.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", "").strip()
    if raw.isdigit() and 0 < int(raw) <= 100:
        return int(raw)
    return AUTOCOMPACT_DEFAULT_PCT


def bands(threshold: int) -> tuple[int, ...]:
    """Ascending pre-warning bands just below the compact threshold.

    Distinct and clamped to >=1; offsets that collapse into the same band (very
    low thresholds) dedupe rather than fire twice at one level.
    """
    return tuple(sorted({max(1, threshold - off) for off in BAND_OFFSETS}))


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
    threshold = autocompact_pct()

    marker = _marker(session_id)
    band = max((b for b in bands(threshold) if pct >= b), default=0)

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
                        pct=pct, tokens=tokens, window=window, threshold=threshold
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
