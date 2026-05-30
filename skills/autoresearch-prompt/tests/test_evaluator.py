# ABOUTME: Tests for evaluator: scoring, JSON parsing, error handling
# ABOUTME: Covers compute_score with weights, parse_llm_output, evaluate_example with mocks

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
        assert resp.fields["action"] == "extract"
        assert resp.fields["category"] == "AI Agents and Tools"

    def test_fenced_json(self):
        raw = '```json\n{"action": "skip", "reason": "job listings"}\n```'
        resp = parse_llm_output(raw)
        assert resp.fields["action"] == "skip"

    def test_fenced_no_lang(self):
        raw = '```\n{"action": "extract", "category": "Dev"}\n```'
        resp = parse_llm_output(raw)
        assert resp.fields["action"] == "extract"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_llm_output("not json at all")


class TestComputeScore:
    def test_perfect_score_equal_weights(self):
        """All fields correct, equal weights -> score = 1.0."""
        results = []
        # 6 correct extracts with correct categories
        for _ in range(6):
            r = ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "extract",
                        "expected_category": "Cat",
                    }
                ),
                field_correct={"action": True, "category": True},
            )
            results.append(r)
        # 14 correct skips (no category field)
        for _ in range(14):
            r = ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "skip",
                    }
                ),
                field_correct={"action": True},
            )
            results.append(r)

        summary = compute_score(results)
        assert summary.total == 20
        assert summary.field_accuracies["action"] == 1.0
        assert summary.field_accuracies["category"] == 1.0
        assert summary.score == 1.0
        assert summary.errors == 0

    def test_explicit_weights(self):
        """Weights = {action: 0.6, category: 0.4} reproduces original formula."""
        results = []
        # 16/20 correct actions, 4/6 correct categories
        for i in range(6):
            r = ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "extract",
                        "expected_category": "Cat",
                    }
                ),
                field_correct={"action": i < 4, "category": i < 4},
            )
            results.append(r)
        for i in range(14):
            r = ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "skip",
                    }
                ),
                field_correct={"action": i < 12},
            )
            results.append(r)

        weights = {"action": 0.6, "category": 0.4}
        summary = compute_score(results, weights)
        # action: 16/20 = 0.8, category: 4/6 = 0.6667
        assert summary.field_accuracies["action"] == 0.8
        assert summary.field_accuracies["category"] == 0.6667
        expected_score = round((0.6 * 0.8 + 0.4 * 0.6667) / 1.0, 4)
        assert summary.score == expected_score

    def test_no_comparisons_for_field(self):
        """When no examples have a field, accuracy = 1.0 (vacuous truth)."""
        results = [
            ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "skip",
                    }
                ),
                field_correct={"action": True},
            )
        ]
        summary = compute_score(results)
        # Only "action" field exists
        assert summary.field_accuracies["action"] == 1.0
        assert "category" not in summary.field_accuracies

    def test_errors_counted(self):
        results = [
            ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "skip",
                    }
                ),
                parse_error=True,
                error_message="API error",
            )
        ]
        summary = compute_score(results)
        assert summary.errors == 1

    def test_weights_filter_fields(self):
        """Weights only score the specified fields, ignoring others."""
        results = [
            ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "extract",
                        "expected_category": "Cat",
                        "expected_content": "some insight",
                    }
                ),
                field_correct={"action": True, "category": True, "content": False},
            )
        ]
        # Score only action+category -> 1.0 (both correct)
        summary = compute_score(results, weights={"action": 0.6, "category": 0.4})
        assert summary.score == 1.0
        # content accuracy still reported
        assert summary.field_accuracies["content"] == 0.0


class TestCost:
    def _results_with_tokens(self, input_tokens: int, output_tokens: int) -> list[ExampleResult]:
        return [
            ExampleResult(
                example=EvalExample.model_validate(
                    {
                        "from": "a",
                        "subject": "s",
                        "content": "c",
                        "expected_action": "skip",
                    }
                ),
                field_correct={"action": True},
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        ]

    def test_cost_uses_actual_model_pricing(self):
        """Cost computed with the price of the model actually passed in."""
        # 2,000,000 input + 1,000,000 output tokens, haiku = (1.00, 5.00) per 1M
        results = self._results_with_tokens(2_000_000, 1_000_000)
        summary = compute_score(results, model="claude-haiku-4-5-20251001")
        # (2_000_000 * 1.00 + 1_000_000 * 5.00) / 1_000_000 = 2.0 + 5.0 = 7.0
        assert summary.cost_usd == 7.0

    def test_cost_zero_for_unknown_model(self):
        """Unknown model -> (0, 0) pricing -> cost 0.0, no crash."""
        results = self._results_with_tokens(2_000_000, 1_000_000)
        summary = compute_score(results, model="claude-opus-does-not-exist")
        assert summary.cost_usd == 0.0


class TestEvaluateExample:
    def test_correct_extract(
        self, sample_extract_example, sample_prompt_md, mock_anthropic_client
    ):
        result = evaluate_example(
            mock_anthropic_client,
            sample_extract_example,
            prompt_path=sample_prompt_md,
        )
        assert result.field_correct["action"] is True
        assert result.field_correct["category"] is True
        assert result.parse_error is False
        assert result.latency_ms >= 0

    def test_correct_skip(self, sample_skip_example, sample_prompt_md):
        client = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text='{"action": "skip", "reason": "not relevant"}')]
        response.usage.input_tokens = 80
        response.usage.output_tokens = 30
        client.messages.create.return_value = response

        result = evaluate_example(client, sample_skip_example, prompt_path=sample_prompt_md)
        assert result.field_correct["action"] is True
        # skip examples don't have expected_category, so no category in field_correct
        assert "category" not in result.field_correct

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
                "from": "A <a@b.com>",
                "subject": "S1",
                "content": "C1",
                "expected_action": "skip",
            },
            {
                "from": "B <b@c.com>",
                "subject": "S2",
                "content": "C2",
                "expected_action": "extract",
                "expected_category": "Dev",
            },
        ]
        path = tmp_path / "eval.jsonl"
        path.write_text("\n".join(json.dumps(d) for d in data), encoding="utf-8")

        examples = load_eval_set(path)
        assert len(examples) == 2
        assert examples[0].inputs["from"] == "A <a@b.com>"
        assert examples[1].expected["category"] == "Dev"
