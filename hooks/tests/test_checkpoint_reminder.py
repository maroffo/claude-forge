#!/usr/bin/env python3
# ABOUTME: Tests for checkpoint-reminder.py, session-count checkpoints on pending change contracts
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_checkpoint_reminder.py

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "checkpoint-reminder.py")

CONTRACT_PENDING = """# Harness Change Contract: sample

## Component

Something.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
"""

CONTRACT_FILLED = CONTRACT_PENDING + "| 2026-08-01 | 12 sessions | metric moved | kept |\n"


def run_hook(project_dir):
    payload = json.dumps({"hook_event_name": "SessionStart", "cwd": project_dir})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=project_dir)
    proc = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True,
        timeout=30, env=env, cwd=project_dir,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def make_repo(tmp, contracts=None, trace_dates=None):
    hc = os.path.join(tmp, "quality_reports", "harness_changes")
    tr = os.path.join(tmp, "quality_reports", "traces")
    os.makedirs(hc)
    os.makedirs(tr)
    for name, content in (contracts or {}).items():
        with open(os.path.join(hc, name), "w") as f:
            f.write(content)
    for i, date in enumerate(trace_dates or []):
        with open(os.path.join(tr, f"{date}_session{i}.jsonl"), "w") as f:
            f.write("{}\n")
    return tmp


def test_no_quality_reports_is_silent():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_hook(tmp) == ""
    print("PASS  no quality_reports -> silent")


def test_below_threshold_is_silent():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(
            tmp,
            contracts={"2026-07-05_sample.md": CONTRACT_PENDING},
            trace_dates=["2026-07-06", "2026-07-07", "2026-07-08"],
        )
        assert run_hook(tmp) == ""
    print("PASS  3 sessions -> silent")


def test_five_sessions_prompts_score_check():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(
            tmp,
            contracts={"2026-07-05_sample.md": CONTRACT_PENDING},
            trace_dates=[f"2026-07-{d:02d}" for d in range(6, 11)],
        )
        out = run_hook(tmp)
        assert "SCORE" in out, out
        assert "2026-07-05_sample" in out, out
    print("PASS  5 sessions -> SCORE spot-check reminder")


def test_ten_sessions_prompts_result_rows():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(
            tmp,
            contracts={"2026-07-05_sample.md": CONTRACT_PENDING},
            trace_dates=[f"2026-07-{d:02d}" for d in range(6, 16)],
        )
        out = run_hook(tmp)
        assert "harness-mechanic" in out, out
        assert "Result" in out, out
    print("PASS  10 sessions -> Result rows + harness-mechanic reminder")


def test_filled_contract_is_silent():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(
            tmp,
            contracts={"2026-07-05_sample.md": CONTRACT_FILLED},
            trace_dates=[f"2026-07-{d:02d}" for d in range(6, 16)],
        )
        assert run_hook(tmp) == ""
    print("PASS  filled Result row -> silent")


def test_template_and_same_day_traces_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(
            tmp,
            contracts={
                "TEMPLATE.md": CONTRACT_PENDING,
                "2026-07-05_sample.md": CONTRACT_PENDING,
            },
            # Same-day traces are the sessions that authored the contract: not evidence.
            trace_dates=["2026-07-05"] * 6,
        )
        assert run_hook(tmp) == ""
    print("PASS  TEMPLATE.md and same-day traces ignored")


if __name__ == "__main__":
    test_no_quality_reports_is_silent()
    test_below_threshold_is_silent()
    test_five_sessions_prompts_score_check()
    test_ten_sessions_prompts_result_rows()
    test_filled_contract_is_silent()
    test_template_and_same_day_traces_ignored()
    print("PASS  checkpoint-reminder (6 cases)")
