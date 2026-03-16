# ABOUTME: Tests for evaluator: scoring, JSON parsing, error handling
# ABOUTME: Covers compute_score, parse_llm_output, evaluate_example with mocks

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from autoresearch_prompt.evaluator import (
    compute_score,
    evaluate_example,
    load_eval_set,
    parse_llm_output,
)
from autoresearch_prompt.models import EvalExample, ExampleResult


class TestParseLLMOutput:
    def test_plain_json(self):
        raw = (
            '{"action": "extract", "category": "AI Agents and Tools",'
            ' "content": "insight", "reason": "relevant"}'
        )
        resp = parse_llm_output(raw)
        assert resp.action == "extract"
        assert resp.category == "AI Agents and Tools"

    def test_fenced_json(self):
        raw = '```json\n{"action": "skip", "reason": "job listings"}\n```'
        resp = parse_llm_output(raw)
        assert resp.action == "skip"

    def test_fenced_no_lang(self):
        raw = '```\n{"action": "extract", "category": "Dev"}\n```'
        resp = parse_llm_output(raw)
        assert resp.action == "extract"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_llm_output("not json at all")


class TestComputeScore:
    def test_perfect_score(self):
        results = []
        # 6 correct extracts with correct categories
        for _ in range(6):
            r = ExampleResult(
                example=EvalExample.model_validate({
                    "from": "a", "subject": "s", "content": "c",
                    "expected_action": "extract", "expected_category": "Cat",
                }),
                action_correct=True,
                category_correct=True,
            )
            results.append(r)
        # 14 correct skips
        for _ in range(14):
            r = ExampleResult(
                example=EvalExample.model_validate({
                    "from": "a", "subject": "s", "content": "c",
                    "expected_action": "skip",
                }),
                action_correct=True,
                category_correct=None,
            )
            results.append(r)

        summary = compute_score(results)
        assert summary.total == 20
        assert summary.extract_accuracy == 1.0
        assert summary.category_accuracy == 1.0
        assert summary.score == 1.0
        assert summary.errors == 0

    def test_formula_weights(self):
        """Score = 0.6 * extract_acc + 0.4 * category_acc."""
        results = []
        # 16/20 correct actions = 0.8 extract_acc
        for i in range(20):
            r = ExampleResult(
                example=EvalExample.model_validate({
                    "from": "a", "subject": "s", "content": "c",
                    "expected_action": "skip",
                }),
                action_correct=i < 16,
            )
            results.append(r)

        summary = compute_score(results)
        assert summary.extract_accuracy == 0.8
        # No category comparisons -> category_accuracy = 1.0
        assert summary.category_accuracy == 1.0
        expected_score = round(0.6 * 0.8 + 0.4 * 1.0, 4)
        assert summary.score == expected_score

    def test_no_category_comparisons(self):
        """When all examples are skips, category_accuracy = 1.0."""
        results = [
            ExampleResult(
                example=EvalExample.model_validate({
                    "from": "a", "subject": "s", "content": "c",
                    "expected_action": "skip",
                }),
                action_correct=True,
            )
        ]
        summary = compute_score(results)
        assert summary.category_accuracy == 1.0

    def test_errors_counted(self):
        results = [
            ExampleResult(
                example=EvalExample.model_validate({
                    "from": "a", "subject": "s", "content": "c",
                    "expected_action": "skip",
                }),
                parse_error=True,
                error_message="API error",
            )
        ]
        summary = compute_score(results)
        assert summary.errors == 1


class TestEvaluateExample:
    def test_correct_extract(
        self, sample_extract_example, sample_prompt_md, mock_anthropic_client
    ):
        result = evaluate_example(
            mock_anthropic_client,
            sample_extract_example,
            prompt_path=sample_prompt_md,
        )
        assert result.action_correct is True
        assert result.category_correct is True
        assert result.parse_error is False
        assert result.latency_ms >= 0  # mock returns instantly

    def test_correct_skip(self, sample_skip_example, sample_prompt_md):
        client = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text='{"action": "skip", "reason": "not relevant"}')]
        response.usage.input_tokens = 80
        response.usage.output_tokens = 30
        client.messages.create.return_value = response

        result = evaluate_example(client, sample_skip_example, prompt_path=sample_prompt_md)
        assert result.action_correct is True
        assert result.category_correct is None

    def test_api_error_does_not_crash(self, sample_extract_example, sample_prompt_md):
        import anthropic as anthropic_mod

        client = MagicMock()
        client.messages.create.side_effect = anthropic_mod.APIError(
            message="rate limit",
            request=MagicMock(),
            body=None,
        )

        result = evaluate_example(client, sample_extract_example, prompt_path=sample_prompt_md)
        assert result.parse_error is True
        assert "API error" in result.error_message

    def test_malformed_json_does_not_crash(self, sample_extract_example, sample_prompt_md):
        client = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text="This is not JSON")]
        response.usage.input_tokens = 100
        response.usage.output_tokens = 20
        client.messages.create.return_value = response

        result = evaluate_example(client, sample_extract_example, prompt_path=sample_prompt_md)
        assert result.parse_error is True
        assert "JSON parse error" in result.error_message


class TestLoadEvalSet:
    def test_load_from_file(self, tmp_path):
        data = [
            {
                "from": "A <a@b.com>", "subject": "S1",
                "content": "C1", "expected_action": "skip",
            },
            {
                "from": "B <b@c.com>", "subject": "S2",
                "content": "C2", "expected_action": "extract",
                "expected_category": "Dev",
            },
        ]
        path = tmp_path / "eval.jsonl"
        path.write_text("\n".join(json.dumps(d) for d in data), encoding="utf-8")

        examples = load_eval_set(path)
        assert len(examples) == 2
        assert examples[0].from_sender == "A <a@b.com>"
        assert examples[1].expected_category == "Dev"
