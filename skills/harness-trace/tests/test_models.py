# ABOUTME: Tests for trace schema Pydantic models
# ABOUTME: Validates TraceEntry parsing, step data models, serialization

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from harness_trace.models import (
    SCHEMA_VERSION,
    ImplementData,
    RefineData,
    ReviewData,
    ScoreData,
    SummaryData,
    TraceEntry,
    UatData,
    VerifyData,
    parse_trace_entry,
    validate_step_data,
)


class TestTraceEntry:
    def test_create_minimal(self):
        entry = TraceEntry(
            session="test",
            ts=datetime(2026, 3, 31, tzinfo=UTC),
            step="SCORE",
        )
        assert entry.v == SCHEMA_VERSION
        assert entry.session == "test"
        assert entry.step == "SCORE"
        assert entry.data == {}

    def test_create_with_data(self):
        entry = TraceEntry(
            session="test",
            ts=datetime(2026, 3, 31, tzinfo=UTC),
            step="SCORE",
            data={"score": 87, "threshold": 80, "gate": "commit"},
        )
        assert entry.data["score"] == 87

    def test_to_jsonl(self):
        entry = TraceEntry(
            session="test",
            ts=datetime(2026, 3, 31, tzinfo=UTC),
            step="VERIFY",
            data={"tests_pass": True},
        )
        jsonl = entry.to_jsonl()
        assert '"step":"VERIFY"' in jsonl
        assert '"tests_pass":true' in jsonl

    def test_roundtrip(self):
        entry = TraceEntry(
            session="roundtrip-test",
            ts=datetime(2026, 3, 31, 12, 0, 0, tzinfo=UTC),
            step="IMPLEMENT",
            data={"agents": ["software-engineer"], "files_changed": 3},
        )
        jsonl = entry.to_jsonl()
        parsed = parse_trace_entry(jsonl)
        assert parsed.session == "roundtrip-test"
        assert parsed.step == "IMPLEMENT"
        assert parsed.data["files_changed"] == 3

    def test_invalid_step_rejected(self):
        with pytest.raises(Exception):
            TraceEntry(
                session="test",
                ts=datetime(2026, 3, 31, tzinfo=UTC),
                step="INVALID_STEP",
            )


class TestStepDataModels:
    def test_refine_data(self):
        data = RefineData(ambiguities_found=3, questions_asked=2)
        assert data.ambiguities_found == 3

    def test_verify_data_defaults(self):
        data = VerifyData()
        assert data.tests_pass is False
        assert data.retries == 0

    def test_review_data_findings(self):
        data = ReviewData(
            agents=["architecture-reviewer"],
            findings={"CRITICAL": 0, "MAJOR": 1, "MINOR": 2},
        )
        assert data.findings["MAJOR"] == 1

    def test_score_data(self):
        data = ScoreData(score=87, threshold=80, gate="commit")
        assert data.gate == "commit"

    def test_implement_data(self):
        data = ImplementData(
            agents=["software-engineer"],
            files_changed=4,
            subtask_count=2,
        )
        assert len(data.agents) == 1

    def test_summary_data(self):
        data = SummaryData(
            tokens_in=45000,
            tokens_out=12000,
            model="claude-opus-4-6",
            duration_min=26,
            files_changed=4,
            final_score=87,
        )
        assert data.model == "claude-opus-4-6"

    def test_uat_data(self):
        data = UatData(performed=True, items=3, passed=3, failed=0)
        assert data.performed is True


class TestValidateStepData:
    def test_valid_score_data(self):
        result = validate_step_data("SCORE", {"score": 90, "threshold": 80, "gate": "pr"})
        assert isinstance(result, ScoreData)
        assert result.score == 90

    def test_unknown_step_returns_none(self):
        result = validate_step_data("PRESENT", {})
        assert result is None

    def test_extra_fields_ignored(self):
        result = validate_step_data("VERIFY", {
            "tests_pass": True,
            "unexpected_field": "value",
        })
        assert isinstance(result, VerifyData)
        assert result.tests_pass is True
