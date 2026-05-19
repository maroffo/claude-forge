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


class TestToolUseExtraction:
    """Tests for the tool_use-driven extraction path (high precision)."""

    def test_emits_route_for_every_agent_call(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        routes = [e for e in entries if e.step == "ROUTE"]
        # Two Agent calls in the fixture: architecture-reviewer + software-engineer.
        assert len(routes) == 2
        targets = {r.data.get("target") for r in routes}
        assert "architecture-reviewer" in targets
        assert "software-engineer" in targets

    def test_reviewer_agent_emits_review(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        reviews = [e for e in entries if e.step == "REVIEW"]
        assert len(reviews) == 1
        assert reviews[0].data.get("agents") == ["architecture-reviewer"]

    def test_software_engineer_does_not_emit_review(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        reviews = [e for e in entries if e.step == "REVIEW"]
        assert all("software-engineer" not in (r.data.get("agents") or []) for r in reviews)

    def test_bash_pytest_emits_verify(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        verifies = [e for e in entries if e.step == "VERIFY"]
        assert len(verifies) >= 1

    def test_bash_ast_grep_emits_blast_radius(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        blast = [e for e in entries if e.step == "BLAST_RADIUS"]
        assert len(blast) == 1
        assert blast[0].data.get("triggered") is True

    def test_webfetch_arxiv_emits_research(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        research = [e for e in entries if e.step == "RESEARCH"]
        assert len(research) == 1
        assert research[0].data.get("sources_consulted") == 1

    def test_summary_metrics_populated(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        summary = next(e for e in entries if e.step == "SUMMARY")
        data = summary.data
        assert data.get("files_changed") == 2  # Edit + Write
        metrics = data.get("metrics")
        assert metrics is not None
        traj = metrics["trajectory_efficiency"]
        # 2 edits + 2 bash + 2 agent + 1 webfetch + 1 askuserq = 8 tool calls
        assert traj["tool_calls"] == 8
        assert traj["edits"] == 2
        assert traj["executions"] == 2  # Bash calls
        assert metrics["verification_strength"]["oracles_count"] == 1
        assert metrics["safety_compliance"]["hitl_gates_hit"] == 1
        assert metrics["replayability"]["full_trace_captured"] is True

    def test_text_fallback_picks_up_score(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        scores = [e for e in entries if e.step == "SCORE"]
        assert len(scores) == 1
        assert scores[0].data.get("score") == 92

    def test_chat_only_session_yields_nothing(self, tmp_path: Path):
        """Pure chat without tool_use must not produce a misleading SUMMARY."""
        f = tmp_path / "chat.jsonl"
        with f.open("w") as fp:
            fp.write(json.dumps({
                "type": "assistant",
                "timestamp": 1715900000000,
                "message": {"content": [{"type": "text", "text": "ciao, come va?"}]},
            }) + "\n")
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
