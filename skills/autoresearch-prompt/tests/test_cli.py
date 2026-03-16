# ABOUTME: Tests for CLI argument parsing, evaluate and classify subcommand output
# ABOUTME: Covers _parse_args, stdout format, stdin JSON input, error cases

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from autoresearch_prompt.cli import _parse_args, main
from autoresearch_prompt.models import LLMResponse, RunSummary


class TestParseArgs:
    def test_evaluate_defaults(self):
        args = _parse_args(["evaluate"])
        assert args.command == "evaluate"
        assert args.prompt is None
        assert args.eval_set is None

    def test_evaluate_with_paths(self, tmp_path):
        prompt = tmp_path / "p.md"
        evalset = tmp_path / "e.jsonl"
        args = _parse_args([
            "evaluate",
            "--prompt", str(prompt),
            "--eval-set", str(evalset),
            "--model", "claude-sonnet-4-5-20250514",
        ])
        assert args.prompt == prompt
        assert args.eval_set == evalset
        assert args.model == "claude-sonnet-4-5-20250514"

    def test_classify_with_args(self):
        args = _parse_args([
            "classify",
            "--from", "Test <t@x.com>",
            "--subject", "AI stuff",
            "--content", "Some content",
        ])
        assert args.command == "classify"
        assert args.from_sender == "Test <t@x.com>"
        assert args.subject == "AI stuff"

    def test_no_command_fails(self):
        with pytest.raises(SystemExit):
            _parse_args([])


class TestMainEvaluate:
    def test_output_format(self):
        summary = RunSummary(
            total=20,
            correct_actions=18,
            correct_categories=5,
            category_comparisons=6,
            extract_accuracy=0.9,
            category_accuracy=0.8333,
            score=0.8733,
            errors=1,
            total_input_tokens=2000,
            total_output_tokens=500,
            cost_usd=0.0045,
            avg_latency_ms=350,
        )

        with (
            patch("autoresearch_prompt.cli.run_evaluation", return_value=summary),
            patch("sys.stdout", new_callable=StringIO) as mock_out,
        ):
            main(["evaluate"])

        output = mock_out.getvalue()
        assert "score: 0.87" in output
        assert "extract_acc: 0.90" in output
        assert "category_acc: 0.83" in output
        assert "cost: $0.0045" in output
        assert "latency_ms: 350" in output
        assert "errors: 1" in output
        assert "total: 20" in output


class TestMainClassify:
    def test_classify_with_args(self):
        response = LLMResponse(
            action="extract",
            category="AI Agents and Tools",
            content="Key insight about AI firewalls",
            reason="technical pattern",
        )

        with (
            patch(
                "autoresearch_prompt.cli.classify_single",
                return_value=response,
            ),
            patch("sys.stdout", new_callable=StringIO) as mock_out,
        ):
            main([
                "classify",
                "--from", "Test <t@x.com>",
                "--subject", "AI Firewall",
                "--content", "Reverse proxy for AI traffic",
            ])

        output = json.loads(mock_out.getvalue())
        assert output["action"] == "extract"
        assert output["category"] == "AI Agents and Tools"

    def test_classify_from_stdin(self):
        response = LLMResponse(action="skip", reason="job listings")
        stdin_data = json.dumps({
            "from": "Jobs <j@x.com>",
            "subject": "68 Hot Jobs",
            "content": "Apply now",
        })

        with (
            patch(
                "autoresearch_prompt.cli.classify_single",
                return_value=response,
            ),
            patch("sys.stdin", StringIO(stdin_data)),
            patch("sys.stdout", new_callable=StringIO) as mock_out,
        ):
            main(["classify"])

        output = json.loads(mock_out.getvalue())
        assert output["action"] == "skip"

    def test_classify_empty_stdin_exits(self):
        with (
            patch("sys.stdin", StringIO("")),
            pytest.raises(SystemExit),
        ):
            main(["classify"])
