#!/usr/bin/env python3
# ABOUTME: SessionStart reminder that counts traced sessions since the oldest pending change contract
# ABOUTME: Nudges the 5-session SCORE spot-check and the 10-session Result-row/harness-mechanic checkpoint

"""Session-count checkpoints for harness change contracts.

Change contracts (quality_reports/harness_changes/) predict improvements that
must be verified after 5-20 sessions, but nothing counts sessions for you.
This hook does: it finds contracts whose Result table is still empty, counts
trace files dated after the oldest one, and prints a reminder at the 5- and
10-session thresholds. Filling the Result rows silences it by construction.

Fail-open: any error exits 0 with no output. Stdout is injected into session
context on SessionStart, so the message stays short.
"""

import os
import re
import sys
from pathlib import Path

DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})_")
RESULT_ROW = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|", re.MULTILINE)
SCORE_CHECK_AT = 5
RESULT_ROWS_AT = 10


def pending_contracts(contracts_dir: Path) -> list[tuple[str, str]]:
    """(date, slug) for dated contracts whose Result section has no data row."""
    pending = []
    for path in sorted(contracts_dir.glob("*.md")):
        m = DATE_PREFIX.match(path.name)
        if not m:
            continue  # TEMPLATE.md and other undated files
        text = path.read_text(errors="replace")
        _, _, result_section = text.partition("## Result")
        if not RESULT_ROW.search(result_section):
            pending.append((m.group(1), path.stem))
    return pending


def sessions_since(traces_dir: Path, date: str) -> int:
    """Trace files strictly newer than `date` (same-day traces authored the contract)."""
    count = 0
    for path in traces_dir.glob("*.jsonl"):
        m = DATE_PREFIX.match(path.name)
        if m and m.group(1) > date:
            count += 1
    return count


def main() -> None:
    base = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    contracts_dir = base / "quality_reports" / "harness_changes"
    traces_dir = base / "quality_reports" / "traces"
    if not contracts_dir.is_dir() or not traces_dir.is_dir():
        return

    pending = pending_contracts(contracts_dir)
    if not pending:
        return

    oldest_date = min(date for date, _ in pending)
    n = sessions_since(traces_dir, oldest_date)
    if n < SCORE_CHECK_AT:
        return

    slugs = ", ".join(slug for _, slug in pending[:3])
    more = f" (+{len(pending) - 3} more)" if len(pending) > 3 else ""
    print(
        f"[checkpoint-reminder] {n} sessions traced since the oldest pending "
        f"change contract ({slugs}{more})."
    )
    if n >= RESULT_ROWS_AT:
        print(
            "Checkpoint due: fill the Result rows in quality_reports/harness_changes/ "
            "and run /harness-mechanic to close the loop."
        )
    else:
        print(
            "Spot-check the newest traces: do SCORE events appear, and do VERIFY/REVIEW "
            "entries carry real outcomes? (contract falsification window)"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open: a broken reminder must never break a session
    sys.exit(0)
