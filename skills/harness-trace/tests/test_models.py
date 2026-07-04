# ABOUTME: Tests for trace schema Pydantic models
# ABOUTME: Validates TraceEntry parsing, step data models, serialization

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from harness_trace.models import (
    SCHEMA_VERSION,
    HarnessMetrics,
    ImplementData,
    PermissionEventData,
    RefineData,
    RejectedAlternative,
    ReviewData,
    RouteData,
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
        # Tri-state: unknown (None) by default, never a fabricated False.
        data = VerifyData()
        assert data.tests_pass is None
        assert data.lint_clean is None
        assert data.build_ok is None
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


class TestSchemaV2:
    def test_schema_version_is_2(self):
        assert SCHEMA_VERSION == 2

    def test_rejected_alternative_on_entry(self):
        entry = TraceEntry(
            session="test",
            ts=datetime(2026, 5, 19, tzinfo=UTC),
            step="IMPLEMENT",
            rejected_alternatives=[
                RejectedAlternative(
                    description="rewrite extractor in regex-free parser",
                    reason_rejected="out of scope, deferred",
                    cost_estimate="high effort",
                ),
            ],
        )
        assert len(entry.rejected_alternatives) == 1
        assert entry.rejected_alternatives[0].reason_rejected.startswith("out of scope")

    def test_rejected_alternatives_default_none(self):
        # Default is None (not []) so empty rows omit the field on the wire.
        entry = TraceEntry(
            session="test", ts=datetime(2026, 5, 19, tzinfo=UTC), step="REFINE",
        )
        assert entry.rejected_alternatives is None
        # exclude_none on serialize must drop the empty field.
        assert "rejected_alternatives" not in entry.to_jsonl()

    def test_permission_event_step(self):
        entry = TraceEntry(
            session="test",
            ts=datetime(2026, 5, 19, tzinfo=UTC),
            step="PERMISSION_EVENT",
            data={
                "tool": "Bash",
                "action": "rm -rf node_modules",
                "outcome": "denied",
                "reason": "destructive-action-guard",
            },
        )
        validated = validate_step_data("PERMISSION_EVENT", entry.data)
        assert isinstance(validated, PermissionEventData)
        assert validated.outcome == "denied"

    def test_permission_event_invalid_outcome(self):
        with pytest.raises(Exception):
            PermissionEventData(tool="Bash", action="ls", outcome="maybe")

    def test_route_step(self):
        entry = TraceEntry(
            session="test",
            ts=datetime(2026, 5, 19, tzinfo=UTC),
            step="ROUTE",
            data={
                "router": "routing-advisor",
                "target": "architecture-reviewer",
                "alternatives_considered": ["security-reviewer", "performance-reviewer"],
                "decision_basis": "*.py file pattern",
            },
        )
        validated = validate_step_data("ROUTE", entry.data)
        assert isinstance(validated, RouteData)
        assert validated.target == "architecture-reviewer"
        assert "security-reviewer" in validated.alternatives_considered

    def test_summary_with_harness_metrics(self):
        data = SummaryData(
            tokens_in=45000,
            tokens_out=12000,
            model="claude-opus-4-7",
            duration_min=42,
            files_changed=6,
            final_score=92,
            metrics=HarnessMetrics(
                trajectory_efficiency={"tool_calls": 87, "tokens": 57000, "edits": 6},
                safety_compliance={"permission_denials": 1, "hitl_gates_hit": 0},
                replayability={"full_trace_captured": True},
            ),
        )
        assert data.metrics is not None
        assert data.metrics.trajectory_efficiency["edits"] == 6
        assert data.metrics.recovery_ability is None  # not measured

    def test_summary_without_metrics_backcompat(self):
        # Existing v1 callers should still be able to skip the metrics field.
        data = SummaryData(tokens_in=100, tokens_out=50, model="x")
        assert data.metrics is None

    def test_v2_jsonl_roundtrip(self):
        entry = TraceEntry(
            session="rt",
            ts=datetime(2026, 5, 19, 12, 0, 0, tzinfo=UTC),
            step="ROUTE",
            data={"router": "r", "target": "t"},
            rejected_alternatives=[
                RejectedAlternative(description="d", reason_rejected="r"),
            ],
        )
        parsed = parse_trace_entry(entry.to_jsonl())
        assert parsed.v == 2
        assert parsed.step == "ROUTE"
        assert len(parsed.rejected_alternatives) == 1
