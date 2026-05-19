# ABOUTME: Tests for session JSONL extractor
# ABOUTME: Validates step detection, data extraction, and trace output

from __future__ import annotations

import json
from pathlib import Path

from harness_trace.extractor import extract_traces, write_traces
from harness_trace.models import SCHEMA_VERSION


class TestExtractTraces:
    def test_extracts_steps_from_sample_session(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        step_names = [e.step for e in entries]

        assert "REFINE" in step_names
        assert "RESEARCH" in step_names
        assert "IMPLEMENT" in step_names
        assert "VERIFY" in step_names
        assert "REVIEW" in step_names
        assert "SCORE" in step_names
        assert "UAT" in step_names

    def test_extracts_correct_session_slug(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="my-session")
        assert all(e.session == "my-session" for e in entries)

    def test_defaults_slug_to_filename(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl)
        assert all(e.session == "test-session" for e in entries)

    def test_extracts_research_complexity(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        research = next(e for e in entries if e.step == "RESEARCH")
        assert research.data.get("complexity") == "moderate"

    def test_extracts_implement_data(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        impl = next(e for e in entries if e.step == "IMPLEMENT")
        assert impl.data.get("files_changed") == 4
        assert "software-engineer" in impl.data.get("agents", [])

    def test_extracts_verify_data(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        verify = next(e for e in entries if e.step == "VERIFY")
        assert verify.data.get("tests_pass") is True
        assert verify.data.get("lint_clean") is True
        assert verify.data.get("build_ok") is True

    def test_extracts_review_findings(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        review = next(e for e in entries if e.step == "REVIEW")
        findings = review.data.get("findings", {})
        assert findings.get("CRITICAL") == 0
        assert findings.get("MAJOR") == 1
        assert findings.get("MINOR") == 2

    def test_extracts_score(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        score = next(e for e in entries if e.step == "SCORE")
        assert score.data.get("score") == 87

    def test_extracts_uat(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        uat = next(e for e in entries if e.step == "UAT")
        assert uat.data.get("performed") is True

    def test_entries_have_timestamps(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        assert all(e.ts is not None for e in entries)

    def test_entries_have_schema_version(self, sample_session_jsonl: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        assert all(e.v == SCHEMA_VERSION for e in entries)

    def test_empty_session_returns_empty(self, tmp_path: Path):
        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        entries = extract_traces(empty, session_slug="empty")
        assert entries == []

    def test_non_orchestrator_session(self, tmp_path: Path):
        """Session without orchestrator patterns yields no traces."""
        msgs = [
            {"type": "user", "timestamp": 1711900000000, "message": {"content": "hello"}},
            {
                "type": "assistant",
                "timestamp": 1711900001000,
                "message": {"content": "Hi! How can I help?"},
            },
        ]
        f = tmp_path / "chat.jsonl"
        with f.open("w") as fp:
            for m in msgs:
                fp.write(json.dumps(m) + "\n")
        entries = extract_traces(f, session_slug="chat")
        assert entries == []


class TestWriteTraces:
    def test_write_and_read_back(self, sample_session_jsonl: Path, tmp_path: Path):
        entries = extract_traces(sample_session_jsonl, session_slug="test")
        output_path = tmp_path / "trace.jsonl"
        write_traces(entries, output_path)

        lines = output_path.read_text().strip().split("\n")
        assert len(lines) == len(entries)

        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "v" in parsed
            assert "step" in parsed
            assert "session" in parsed
