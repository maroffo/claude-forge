# ABOUTME: Tests for CLI helpers (trace output naming)
# ABOUTME: Extraction date must not leak into filenames: one session = one trace file

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from harness_trace.cli import trace_output_path
from harness_trace.models import TraceEntry


def _entry(ts: datetime) -> TraceEntry:
    return TraceEntry(session="s", ts=ts, step="VERIFY", data={})


class TestTraceOutputPath:
    def test_uses_session_start_date_not_today(self, tmp_path: Path):
        """A session started 2026-07-01 keeps that date no matter when it is extracted."""
        entries = [
            _entry(datetime(2026, 7, 1, 9, 0, tzinfo=UTC)),
            _entry(datetime(2026, 7, 3, 18, 0, tzinfo=UTC)),
        ]
        path = trace_output_path(tmp_path, entries, "abc123")
        assert path.name == "2026-07-01_abc123.jsonl"

    def test_reextraction_converges_on_same_file(self, tmp_path: Path):
        """PreCompact snapshot and later SessionEnd extraction must overwrite, not multiply."""
        early = [_entry(datetime(2026, 7, 1, 9, 0, tzinfo=UTC))]
        late = early + [_entry(datetime(2026, 7, 4, 12, 0, tzinfo=UTC))]
        assert trace_output_path(tmp_path, early, "abc123") == trace_output_path(
            tmp_path, late, "abc123"
        )
