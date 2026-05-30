# ABOUTME: Tests for CLI argument parsing, evaluate and classify subcommand output
# ABOUTME: Covers _parse_args, --weights, dynamic output format, stdin JSON input

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from autoresearch_prompt.cli import _parse_args, _parse_weights, main
from autoresearch_prompt.models import LLMResponse, RunSummary


class TestParseWeights:
    def test_two_fields(self):
        assert _parse_weights("action=0.6,category=0.4") == {
            "action": 0.6,
            "category": 0.4,
        }

    def test_single_field(self):
        assert _parse_weights("action=1.0") == {"action": 1.0}

    def test_spaces_tolerated(self):
        assert _parse_weights("action = 0.6 , category = 0.4") == {
            "action": 0.6,
            "category": 0.4,
        }

    def test_trailing_comma(self):
        assert _parse_weights("action=0.6,") == {"action": 0.6}


class TestParseArgs:
    def test_evaluate_defaults(self):
        args = _parse_args(["evaluate"])
        assert args.command == "evaluate"
        assert args.prompt is None
        assert args.eval_set is None
        assert args.weights is None

    def test_evaluate_with_weights(self):
        args = _parse_args(["evaluate", "--weights", "action=0.6,category=0.4"])
        assert args.weights == "action=0.6,category=0.4"

    def test_evaluate_with_paths(self, tmp_path):
        prompt = tmp_path / "p.md"
        evalset = tmp_path / "e.jsonl"
        args = _parse_args(
            [
                "evaluate",
                "--prompt",
                str(prompt),
                "--eval-set",
                str(evalset),
                "--model",
                "claude-sonnet-4-6",
            ]
        )
        assert args.prompt == prompt
        assert args.eval_set == evalset
        assert args.model == "claude-sonnet-4-6"

    def test_classify_defaults(self):
        args = _parse_args(["classify"])
        assert args.command == "classify"

    def test_no_command_fails(self):
        with pytest.raises(SystemExit):
            _parse_args([])


class TestMainEvaluate:
    def test_output_format_dynamic_fields(self):
        summary = RunSummary(
            total=20,
            field_accuracies={"action": 0.9, "category": 0.8333},
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
        assert "action_acc: 0.90" in output
        assert "category_acc: 0.83" in output
        assert "cost: $0.0045" in output
        assert "latency_ms: 350" in output
        assert "errors: 1" in output
        assert "total: 20" in output

    def test_weights_passed_to_evaluator(self):
        summary = RunSummary(
            total=1,
            field_accuracies={"action": 1.0},
            score=1.0,
            errors=0,
        )

        with (
            patch("autoresearch_prompt.cli.run_evaluation", return_value=summary) as mock_eval,
            patch("sys.stdout", new_callable=StringIO),
        ):
            main(["evaluate", "--weights", "action=0.6,category=0.4"])

        call_kwargs = mock_eval.call_args
        assert call_kwargs.kwargs["weights"] == {"action": 0.6, "category": 0.4}

    def test_weights_filter_output_fields(self):
        """Only fields in --weights appear in output, not all field_accuracies."""
        summary = RunSummary(
            total=20,
            field_accuracies={"action": 0.9, "category": 1.0, "content": 0.0},
            score=0.94,
            errors=0,
        )

        with (
            patch("autoresearch_prompt.cli.run_evaluation", return_value=summary),
            patch("sys.stdout", new_callable=StringIO) as mock_out,
        ):
            main(["evaluate", "--weights", "action=0.6,category=0.4"])

        output = mock_out.getvalue()
        assert "action_acc: 0.90" in output
        assert "category_acc: 1.00" in output
        assert "content_acc" not in output


class TestMainClassify:
    def test_classify_from_stdin(self):
        response = LLMResponse(
            fields={
                "action": "skip",
                "reason": "job listings",
            }
        )
        stdin_data = json.dumps(
            {
                "from": "Jobs <j@x.com>",
                "subject": "68 Hot Jobs",
                "content": "Apply now",
            }
        )

        with (
            patch(
                "autoresearch_prompt.cli.classify_single",
                return_value=response,
            ) as mock_cls,
            patch("sys.stdin", StringIO(stdin_data)),
            patch("sys.stdout", new_callable=StringIO) as mock_out,
        ):
            main(["classify"])

        # Verify fields passed to classify_single
        call_kwargs = mock_cls.call_args
        assert call_kwargs.kwargs["fields"]["from"] == "Jobs <j@x.com>"

        output = json.loads(mock_out.getvalue())
        assert output["action"] == "skip"

    def test_classify_empty_stdin_exits(self):
        with (
            patch("sys.stdin", StringIO("")),
            pytest.raises(SystemExit),
        ):
            main(["classify"])

    def test_classify_arbitrary_fields(self):
        """Non-newsletter fields passed through to classify_single."""
        response = LLMResponse(fields={"message": "fix: resolve typo"})
        stdin_data = json.dumps({"diff": "- old\n+ new", "context": "typo fix"})

        with (
            patch(
                "autoresearch_prompt.cli.classify_single",
                return_value=response,
            ) as mock_cls,
            patch("sys.stdin", StringIO(stdin_data)),
            patch("sys.stdout", new_callable=StringIO) as mock_out,
        ):
            main(["classify"])

        call_kwargs = mock_cls.call_args
        assert call_kwargs.kwargs["fields"]["diff"] == "- old\n+ new"
        output = json.loads(mock_out.getvalue())
        assert output["message"] == "fix: resolve typo"

    def test_classify_invalid_json_exits(self):
        with (
            patch("sys.stdin", StringIO("not json")),
            pytest.raises(SystemExit),
        ):
            main(["classify"])

    def test_classify_array_json_exits(self):
        with (
            patch("sys.stdin", StringIO('[{"a":1}]')),
            pytest.raises(SystemExit),
        ):
            main(["classify"])
