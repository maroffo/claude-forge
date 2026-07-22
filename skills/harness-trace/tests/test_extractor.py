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

    def test_bash_ast_grep_does_not_emit_blast_radius(self, tool_use_session_jsonl: Path):
        """The always-use-sg rule saturates any ast-grep tool signal (15 events in
        session 6ca2d622, 0 in sessions where step 5b actually triggered); only the
        literal BLAST-RADIUS report line is trusted."""
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        assert [e for e in entries if e.step == "BLAST_RADIUS"] == []

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
        # Fixture spans 80s across 9 assistant messages with 10s gaps each (all
        # under the 300s active ceiling), so active_min = 80s // 60 = 1.
        assert traj["active_min"] == 1
        assert metrics["verification_strength"]["oracles_count"] == 1
        assert metrics["safety_compliance"]["hitl_gates_hit"] == 1
        assert metrics["replayability"]["full_trace_captured"] is True

    def test_active_min_clamps_long_idle_gaps(self, tmp_path: Path):
        """A session with a 3-day gap between two messages must not count those days as work."""
        import json as _json
        f = tmp_path / "spread.jsonl"
        # Two assistant messages, one Edit each, separated by 3 days.
        day1_ms = 1715900000000
        day4_ms = day1_ms + 3 * 24 * 60 * 60 * 1000  # +3 days
        with f.open("w") as fp:
            for ts, blocks in [
                (day1_ms, [{"type": "tool_use", "name": "Edit",
                            "input": {"file_path": "/a.py", "old_string": "x", "new_string": "y"}}]),
                (day4_ms, [{"type": "tool_use", "name": "Edit",
                            "input": {"file_path": "/b.py", "old_string": "x", "new_string": "y"}}]),
            ]:
                fp.write(_json.dumps({
                    "type": "assistant", "timestamp": ts,
                    "message": {"content": blocks},
                }) + "\n")
        entries = extract_traces(f, session_slug="spread")
        summary = next(e for e in entries if e.step == "SUMMARY")
        # Calendar span is ~4320 min (3 days). Active work time must be ceiling
        # only: one gap clamped to 300s = 5 min.
        assert summary.data["duration_min"] >= 3 * 24 * 60 - 1  # ~4320 min
        assert summary.data["metrics"]["trajectory_efficiency"]["active_min"] == 5

    def test_active_min_never_exceeds_duration(self, tool_use_session_jsonl: Path):
        entries = extract_traces(tool_use_session_jsonl, session_slug="tu")
        summary = next(e for e in entries if e.step == "SUMMARY")
        assert (
            summary.data["metrics"]["trajectory_efficiency"]["active_min"]
            <= summary.data["duration_min"] + 1  # +1 for floor() rounding tolerance
        )

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


def _write_review_session(tmp_path: Path, report: str) -> Path:
    """Session with one reviewer Agent call whose tool_result carries `report`."""
    msgs = [
        {
            "type": "assistant", "timestamp": 1715900000000,
            "message": {"content": [{
                "type": "tool_use", "id": "tu_r", "name": "Agent",
                "input": {"subagent_type": "dx-reviewer", "description": "review"},
            }]},
        },
        {
            "type": "user", "timestamp": 1715900005000,
            "message": {"content": [{
                "type": "tool_result", "tool_use_id": "tu_r",
                "content": [{"type": "text", "text": report}],
            }]},
        },
    ]
    f = tmp_path / "review-session.jsonl"
    with f.open("w") as fp:
        for m in msgs:
            fp.write(json.dumps(m) + "\n")
    return f


def _write_verify_session(tmp_path: Path, command: str, output: str, is_error: bool = False) -> Path:
    """Session with one Bash verify call whose tool_result carries `output`."""
    msgs = [
        {
            "type": "assistant", "timestamp": 1715900000000,
            "message": {"content": [{
                "type": "tool_use", "id": "tu_v", "name": "Bash",
                "input": {"command": command},
            }]},
        },
        {
            "type": "user", "timestamp": 1715900005000,
            "message": {"content": [{
                "type": "tool_result", "tool_use_id": "tu_v",
                "is_error": is_error,
                "content": [{"type": "text", "text": output}],
            }]},
        },
    ]
    f = tmp_path / "verify-session.jsonl"
    with f.open("w") as fp:
        for m in msgs:
            fp.write(json.dumps(m) + "\n")
    return f


class TestVerifyOutcomeCapture:
    """VERIFY entries must reflect the tool_result outcome, not hard-coded defaults."""

    def _verifies(self, path: Path):
        entries = extract_traces(path, session_slug="tr")
        return [e for e in entries if e.step == "VERIFY"]

    def test_green_pytest_sets_tests_pass_true(self, tool_result_session_jsonl: Path):
        verifies = self._verifies(tool_result_session_jsonl)
        pytest_ok = verifies[0]  # first verify: green pytest
        assert pytest_ok.data.get("tests_pass") is True

    def test_green_make_check_sets_lint_clean_true(self, tool_result_session_jsonl: Path):
        verifies = self._verifies(tool_result_session_jsonl)
        check_ok = verifies[1]  # second verify: make check
        assert check_ok.data.get("lint_clean") is True

    def test_red_pytest_sets_tests_pass_false(self, tool_result_session_jsonl: Path):
        verifies = self._verifies(tool_result_session_jsonl)
        pytest_fail = verifies[2]  # third verify: failing pytest
        assert pytest_fail.data.get("tests_pass") is False

    def test_failure_marker_in_text_overrides_clean_exit(self, tmp_path: Path):
        """`pytest || true` chains exit 0 but the output still says failed."""
        base = 1715900000000
        msgs = [
            {
                "type": "assistant", "timestamp": base,
                "message": {"content": [{
                    "type": "tool_use", "id": "tu_masked", "name": "Bash",
                    "input": {"command": "pytest tests/ || true"},
                }]},
            },
            {
                "type": "user", "timestamp": base + 5_000,
                "message": {"content": [{
                    "type": "tool_result", "tool_use_id": "tu_masked",
                    "is_error": False,
                    "content": [{"type": "text", "text": "==== 3 failed, 9 passed ===="}],
                }]},
            },
        ]
        f = tmp_path / "masked.jsonl"
        with f.open("w") as fp:
            for m in msgs:
                fp.write(json.dumps(m) + "\n")
        verifies = self._verifies(f)
        assert len(verifies) == 1
        assert verifies[0].data.get("tests_pass") is False

    def test_orphan_verify_stays_unknown(self, tool_result_session_jsonl: Path):
        """No tool_result in the stream -> outcome unknown, never a fabricated false."""
        verifies = self._verifies(tool_result_session_jsonl)
        orphan = verifies[3]  # fourth verify: go test with no result
        assert orphan.data.get("tests_pass") is None
        assert orphan.data.get("lint_clean") is None
        assert orphan.data.get("build_ok") is None

    def test_unresolved_fields_stay_unknown_on_green_run(self, tool_result_session_jsonl: Path):
        """A pytest result says nothing about lint or build."""
        verifies = self._verifies(tool_result_session_jsonl)
        pytest_ok = verifies[0]
        assert pytest_ok.data.get("lint_clean") is None
        assert pytest_ok.data.get("build_ok") is None

    def test_fixed_errors_summary_is_not_a_failure(self, tmp_path: Path):
        """ruff-style 'Found 3 errors (3 fixed, 0 remaining).' with exit 0 is green."""
        f = _write_verify_session(
            tmp_path, "make check", "Found 3 errors (3 fixed, 0 remaining).\nAll checks passed"
        )
        verifies = self._verifies(f)
        assert verifies[0].data.get("lint_clean") is True

    def test_compound_command_failure_leaves_axes_unknown(self, tmp_path: Path):
        """'make check && make test' failing can't attribute the failure to one axis."""
        f = _write_verify_session(
            tmp_path, "make check && make test", "something broke", is_error=True
        )
        verifies = self._verifies(f)
        assert verifies[0].data.get("lint_clean") is None
        assert verifies[0].data.get("tests_pass") is None

    def test_compound_command_success_resolves_both_axes(self, tmp_path: Path):
        f = _write_verify_session(
            tmp_path, "make check && make test", "PASS  everything\nok"
        )
        verifies = self._verifies(f)
        assert verifies[0].data.get("lint_clean") is True
        assert verifies[0].data.get("tests_pass") is True

    def test_blank_line_heavy_output_extracts_quickly(self, tmp_path: Path):
        """200 KB of newlines must not trigger quadratic regex backtracking."""
        import time
        f = _write_verify_session(tmp_path, "pytest tests/", "\n" * 200_000 + "1 passed")
        start = time.monotonic()
        verifies = self._verifies(f)
        elapsed = time.monotonic() - start
        assert verifies[0].data.get("tests_pass") is True
        assert elapsed < 2.0, f"extraction took {elapsed:.1f}s: quadratic backtracking regression"


class TestReviewFindingsCapture:
    """REVIEW entries must carry the severity counts from the reviewer's returned report."""

    def test_reviewer_result_populates_findings(self, tool_result_session_jsonl: Path):
        entries = extract_traces(tool_result_session_jsonl, session_slug="tr")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}

    def test_reviewer_without_result_keeps_empty_findings(self, tmp_path: Path):
        """Truncated session: Agent call with no tool_result -> findings stay {}."""
        msgs = [{
            "type": "assistant", "timestamp": 1715900000000,
            "message": {"content": [{
                "type": "tool_use", "id": "tu_r", "name": "Agent",
                "input": {"subagent_type": "security-reviewer", "description": "review"},
            }]},
        }]
        f = tmp_path / "orphan-review.jsonl"
        with f.open("w") as fp:
            for m in msgs:
                fp.write(json.dumps(m) + "\n")
        entries = extract_traces(f, session_slug="orphan")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {}

    def test_section_style_report_counts_bullets(self, tmp_path: Path):
        """Real reviewers write '### MAJOR' sections with bullets, not 'MAJOR: 1'."""
        report = (
            "## DX Review\n\n"
            "### CRITICAL\nNone.\n\n"
            "### MAJOR (internal contradictions)\n"
            "- **README.md:255** contradicts the new rule\n"
            "- **SKILL.md:12** stale reference\n\n"
            "### MINOR\n"
            "- typo in header\n"
        )
        msgs = [
            {
                "type": "assistant", "timestamp": 1715900000000,
                "message": {"content": [{
                    "type": "tool_use", "id": "tu_r", "name": "Agent",
                    "input": {"subagent_type": "dx-reviewer", "description": "review"},
                }]},
            },
            {
                "type": "user", "timestamp": 1715900005000,
                "message": {"content": [{
                    "type": "tool_result", "tool_use_id": "tu_r",
                    "content": [{"type": "text", "text": report}],
                }]},
            },
        ]
        f = tmp_path / "section-review.jsonl"
        with f.open("w") as fp:
            for m in msgs:
                fp.write(json.dumps(m) + "\n")
        entries = extract_traces(f, session_slug="section")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {"CRITICAL": 0, "MAJOR": 2, "MINOR": 1}

    def test_numbered_bullets_are_counted_not_misread_as_counts(self, tmp_path: Path):
        """'### MAJOR\\n1. foo\\n2. bar' is 2 findings, not 'MAJOR: 1'."""
        report = "### MAJOR\n1. first finding\n2. second finding\n\n### MINOR\nNone.\n"
        f = _write_review_session(tmp_path, report)
        entries = extract_traces(f, session_slug="numbered")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {"MAJOR": 2, "MINOR": 0}

    def test_digit_leading_bullet_does_not_fabricate_counts(self, tmp_path: Path):
        """'### MAJOR\\n- 3 unused imports' is 1 finding, not 'MAJOR: 3'."""
        report = "### MAJOR\n- 3 unused imports in extractor.py\n"
        f = _write_review_session(tmp_path, report)
        entries = extract_traces(f, session_slug="digit-bullet")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {"MAJOR": 1}

    def test_bullets_inside_code_fences_are_not_counted(self, tmp_path: Path):
        report = (
            "### MAJOR\n- real finding\n"
            "```\n- quoted bullet inside code\n- another quoted bullet\n```\n"
        )
        f = _write_review_session(tmp_path, report)
        entries = extract_traces(f, session_slug="fenced")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {"MAJOR": 1}

    def test_huge_digit_run_does_not_crash_extraction(self, tmp_path: Path):
        """Crafted 'MAJOR: 9...9' (5000 digits) must not abort extract_traces."""
        report = "MAJOR: " + "9" * 5000
        f = _write_review_session(tmp_path, report)
        entries = extract_traces(f, session_slug="hugeint")  # must not raise
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {}

    def test_unparseable_review_result_keeps_empty_findings(self, tmp_path: Path):
        """Reviewer output without severity counts must not fabricate findings."""
        msgs = [
            {
                "type": "assistant", "timestamp": 1715900000000,
                "message": {"content": [{
                    "type": "tool_use", "id": "tu_r", "name": "Agent",
                    "input": {"subagent_type": "dx-reviewer", "description": "review"},
                }]},
            },
            {
                "type": "user", "timestamp": 1715900005000,
                "message": {"content": [{
                    "type": "tool_result", "tool_use_id": "tu_r",
                    "is_error": False,
                    "content": [{"type": "text", "text": "Everything looks good, ship it."}],
                }]},
            },
        ]
        f = tmp_path / "clean-review.jsonl"
        with f.open("w") as fp:
            for m in msgs:
                fp.write(json.dumps(m) + "\n")
        entries = extract_traces(f, session_slug="clean")
        review = next(e for e in entries if e.step == "REVIEW")
        assert review.data.get("findings") == {}


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


def _commit_session(tmp_path: Path, command: str, result_text: str, is_error: bool = False) -> Path:
    """Build a minimal session: one Bash tool_use + its paired tool_result."""
    f = tmp_path / "commit.jsonl"
    tuid = "toolu_commit_1"
    with f.open("w") as fp:
        fp.write(json.dumps({
            "type": "assistant", "timestamp": 1715900000000,
            "message": {"content": [
                {"type": "tool_use", "id": tuid, "name": "Bash",
                 "input": {"command": command}},
            ]},
        }) + "\n")
        fp.write(json.dumps({
            "type": "user", "timestamp": 1715900001000,
            "message": {"content": [
                {"type": "tool_result", "tool_use_id": tuid,
                 "is_error": is_error, "content": result_text},
            ]},
        }) + "\n")
    return f


class TestVerifyFromPreCommitGate:
    """git commit runs make check (+ make test-e2e, unless docs-only) via the
    pre-commit-gate hook. A landed commit evidences lint; e2e may have been
    skipped and that skip is invisible in the tool_result, so tests_pass stays
    unknown. Failures/denies resolve fail-closed."""

    def test_successful_commit_sets_lint_leaves_tests_unknown(self, tmp_path: Path):
        # `make check` always runs on a landed commit; `make test-e2e` is skipped
        # for docs-only diffs and that skip is invisible here, so tests_pass must
        # stay None rather than fabricate a pass.
        f = _commit_session(
            tmp_path,
            'git commit -m "feat: x"',
            "[feat/branch 049a243] feat: x\n 3 files changed, 10 insertions(+)",
        )
        entries = extract_traces(f, session_slug="c")
        verifies = [e for e in entries if e.step == "VERIFY"]
        assert len(verifies) == 1
        assert verifies[0].data.get("lint_clean") is True
        assert verifies[0].data.get("tests_pass") is None

    def test_commit_with_pytest_in_message_still_counts_as_commit(self, tmp_path: Path):
        # "pytest" in the message must not route to the generic verify branch.
        f = _commit_session(
            tmp_path,
            'git commit -m "add pytest fixtures"',
            "[feat/branch 049a243] add pytest fixtures\n 2 files changed",
        )
        entries = extract_traces(f, session_slug="c")
        verifies = [e for e in entries if e.step == "VERIFY"]
        assert len(verifies) == 1
        assert verifies[0].data.get("lint_clean") is True
        assert verifies[0].data.get("tests_pass") is None

    def test_git_push_does_not_emit_verify(self, tmp_path: Path):
        f = _commit_session(tmp_path, "git push -u origin feat/branch",
                            "To github.com:me/repo.git\n * [new branch] feat/branch")
        entries = extract_traces(f, session_slug="c")
        assert [e for e in entries if e.step == "VERIFY"] == []

    def test_gate_deny_make_check_sets_lint_false(self, tmp_path: Path):
        f = _commit_session(
            tmp_path, 'git commit -m "feat: x"',
            "Pre-commit gate: `make check` failed. Fix lint/vet/test issues.",
            is_error=True,
        )
        entries = extract_traces(f, session_slug="c")
        verify = next(e for e in entries if e.step == "VERIFY")
        assert verify.data.get("lint_clean") is False

    def test_gate_deny_test_e2e_sets_tests_false(self, tmp_path: Path):
        f = _commit_session(
            tmp_path, 'git commit -m "feat: x"',
            "Pre-commit gate: `make test-e2e` failed. Fix failing end-to-end tests.",
            is_error=True,
        )
        entries = extract_traces(f, session_slug="c")
        verify = next(e for e in entries if e.step == "VERIFY")
        assert verify.data.get("tests_pass") is False

    def test_denied_commit_with_spoofed_success_line_fails_closed(self, tmp_path: Path):
        # is_error=True with an embedded fixture success line must NOT read as a
        # pass: the error/deny is authoritative, tests_pass resolves False.
        f = _commit_session(
            tmp_path, 'git commit -m "feat: x"',
            "Pre-commit gate: `make test-e2e` failed.\n[main 1234567] x\n 3 files changed",
            is_error=True,
        )
        entries = extract_traces(f, session_slug="c")
        verify = next(e for e in entries if e.step == "VERIFY")
        assert verify.data.get("tests_pass") is False
        assert verify.data.get("lint_clean") is None

    def test_bypass_commit_does_not_emit_verify(self, tmp_path: Path):
        f = _commit_session(tmp_path, "git commit --no-verify -m x",
                            "[feat/branch 049a243] x\n 1 file changed")
        entries = extract_traces(f, session_slug="c")
        assert [e for e in entries if e.step == "VERIFY"] == []

    def test_nothing_to_commit_leaves_axes_unknown(self, tmp_path: Path):
        f = _commit_session(tmp_path, 'git commit -m x',
                            "nothing to commit, working tree clean", is_error=True)
        entries = extract_traces(f, session_slug="c")
        verify = next(e for e in entries if e.step == "VERIFY")
        assert verify.data.get("tests_pass") is None
        assert verify.data.get("lint_clean") is None


def _write_text_session(tmp_path: Path, text: str) -> Path:
    """Session with a single assistant text message."""
    f = tmp_path / "text-session.jsonl"
    with f.open("w") as fp:
        fp.write(json.dumps({
            "type": "assistant", "timestamp": 1715900000000,
            "message": {"content": [{"type": "text", "text": text}]},
        }) + "\n")
    return f


class TestSubstepReportExtraction:
    """Literal sub-step report lines (orchestrator-protocol step 1a/1b/1c) emit trace events."""

    def test_localize_report_emits_localize(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "LOCALIZE: planned=3 proposed=3 precision=1.00 recall=0.67 mismatches=none",
        )
        entries = extract_traces(f, session_slug="s")
        loc = next(e for e in entries if e.step == "LOCALIZE")
        assert loc.data.get("planned_count") == 3
        assert loc.data.get("proposed_count") == 3
        assert loc.data.get("precision") == 1.0
        assert loc.data.get("recall") == 0.67
        assert loc.data.get("mismatches") == []

    def test_localize_mismatches_parsed_as_list(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "LOCALIZE: planned=2 proposed=3 precision=0.67 recall=1.00 "
            "mismatches=cmd/main.go,internal/x.go",
        )
        entries = extract_traces(f, session_slug="s")
        loc = next(e for e in entries if e.step == "LOCALIZE")
        assert loc.data.get("mismatches") == ["cmd/main.go", "internal/x.go"]

    def test_reproduce_report_emits_reproduce(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "REPRODUCE: script=scripts/repro_531.sh fails_before_fix=true",
        )
        entries = extract_traces(f, session_slug="s")
        rep = next(e for e in entries if e.step == "REPRODUCE")
        assert rep.data.get("script") == "scripts/repro_531.sh"
        assert rep.data.get("fails_before_fix") is True

    def test_drift_report_emits_drift_check(self, tmp_path: Path):
        f = _write_text_session(tmp_path, "DRIFT: subtask=2b verdict=minor_drift")
        entries = extract_traces(f, session_slug="s")
        drift = next(e for e in entries if e.step == "DRIFT_CHECK")
        assert drift.data.get("subtask_id") == "2b"
        assert drift.data.get("verdict") == "minor_drift"

    def test_executor_report_emits_executor(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "EXECUTOR: pi-exec model=claude-3-5-sonnet-20241022 subtask=95",
        )
        entries = extract_traces(f, session_slug="s")
        executor = next(e for e in entries if e.step == "EXECUTOR")
        assert executor.data.get("executor") == "pi-exec"
        assert executor.data.get("model") == "claude-3-5-sonnet-20241022"
        assert executor.data.get("subtask_id") == "95"

    def test_prose_mentions_do_not_emit_substeps(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "I will localize the files, reproduce the bug, and check for drift "
            "before the next subtask.",
        )
        entries = extract_traces(f, session_slug="s")
        assert [e for e in entries if e.step in ("LOCALIZE", "REPRODUCE", "DRIFT_CHECK", "EXECUTOR")] == []

    def test_partial_localize_line_does_not_emit(self, tmp_path: Path):
        """A LOCALIZE line missing the mandated fields must not create an empty event."""
        f = _write_text_session(tmp_path, "LOCALIZE: planned=3")
        entries = extract_traces(f, session_slug="s")
        assert [e for e in entries if e.step == "LOCALIZE"] == []


class TestBlastRadiusReportExtraction:
    """BLAST_RADIUS is keyed on the literal step-5b report line, not on ast-grep usage."""

    def test_clean_report_emits_blast_radius(self, tmp_path: Path):
        f = _write_text_session(tmp_path, "BLAST-RADIUS: clean (files_checked=12)")
        entries = extract_traces(f, session_slug="s")
        blast = next(e for e in entries if e.step == "BLAST_RADIUS")
        assert blast.data.get("triggered") is True
        assert blast.data.get("files_scanned") == 12
        assert blast.data.get("contradictions") == {}

    def test_findings_report_captures_contradictions(self, tmp_path: Path):
        f = _write_text_session(tmp_path, "BLAST-RADIUS: MAJOR=1 MINOR=2 (files_checked=8)")
        entries = extract_traces(f, session_slug="s")
        blast = next(e for e in entries if e.step == "BLAST_RADIUS")
        assert blast.data.get("triggered") is True
        assert blast.data.get("contradictions") == {"MAJOR": 1, "MINOR": 2}
        assert blast.data.get("files_scanned") == 8

    def test_skipped_report_captures_reason(self, tmp_path: Path):
        f = _write_text_session(tmp_path, "BLAST-RADIUS: skipped (docs-only)")
        entries = extract_traces(f, session_slug="s")
        blast = next(e for e in entries if e.step == "BLAST_RADIUS")
        assert blast.data.get("triggered") is False
        assert blast.data.get("trigger_reason") == "docs-only"

    def test_prose_blast_radius_mention_does_not_emit(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "Next I will check the blast radius of the rename with ast-grep.",
        )
        entries = extract_traces(f, session_slug="s")
        assert [e for e in entries if e.step == "BLAST_RADIUS"] == []


class TestReviewFixes:
    """Regression tests from the 2026-07-15 architecture + security review round."""

    def test_colocated_report_lines_all_emit(self, tmp_path: Path):
        """Protocol co-locates literal lines in one turn; none may shadow another."""
        f = _write_text_session(
            tmp_path,
            "LOCALIZE: planned=2 proposed=2 precision=1.00 recall=1.00 mismatches=none\n"
            "REPRODUCE: script=scripts/repro.sh fails_before_fix=true\n"
            "SCORE: 92/100 (threshold: 80, gate: commit)",
        )
        entries = extract_traces(f, session_slug="s")
        steps = [e.step for e in entries]
        assert "LOCALIZE" in steps
        assert "REPRODUCE" in steps
        assert "SCORE" in steps

    def test_fenced_report_lines_do_not_emit(self, tmp_path: Path):
        """Quoted content inside code fences must not forge trace events."""
        f = _write_text_session(
            tmp_path,
            "Here is what the doc suggests reporting:\n"
            "```\nBLAST-RADIUS: clean (files_checked=42)\n"
            "REPRODUCE: script=x.sh fails_before_fix=true\n"
            "EXECUTOR: pi-exec model=claude-3-5-sonnet subtask=95\n```\n"
            "I have not run these steps yet.",
        )
        entries = extract_traces(f, session_slug="s")
        assert [e for e in entries if e.step in ("BLAST_RADIUS", "REPRODUCE", "EXECUTOR")] == []

    def test_minor_before_major_still_captures_both(self, tmp_path: Path):
        f = _write_text_session(tmp_path, "BLAST-RADIUS: MINOR=2 MAJOR=1 (files_checked=8)")
        entries = extract_traces(f, session_slug="s")
        blast = next(e for e in entries if e.step == "BLAST_RADIUS")
        assert blast.data.get("contradictions") == {"MAJOR": 1, "MINOR": 2}
        assert blast.data.get("files_scanned") == 8

    def test_oversized_script_token_does_not_emit(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "REPRODUCE: script=" + "a" * 5000 + " fails_before_fix=true",
        )
        entries = extract_traces(f, session_slug="s")
        assert [e for e in entries if e.step == "REPRODUCE"] == []

    def test_oversized_executor_token_does_not_emit(self, tmp_path: Path):
        f = _write_text_session(
            tmp_path,
            "EXECUTOR: pi-exec model=" + "m" * 500 + " subtask=95",
        )
        entries = extract_traces(f, session_slug="s")
        assert [e for e in entries if e.step == "EXECUTOR"] == []
