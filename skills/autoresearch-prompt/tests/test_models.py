# ABOUTME: Tests for Pydantic models: serialization, aliases, validation
# ABOUTME: Covers EvalExample from-alias, LLMResponse, ExampleResult, RunSummary

from __future__ import annotations

import json

from autoresearch_prompt.models import EvalExample, ExampleResult, LLMResponse, RunSummary


class TestEvalExample:
    def test_from_alias(self):
        """Field alias 'from' maps to from_sender."""
        data = {
            "from": "Author <a@b.com>",
            "subject": "Test",
            "content": "body",
            "expected_action": "extract",
        }
        ex = EvalExample.model_validate(data)
        assert ex.from_sender == "Author <a@b.com>"

    def test_from_jsonl_line(self):
        """Parse a JSONL line with alias."""
        line = json.dumps({
            "from": "Sender <s@x.com>",
            "subject": "Sub",
            "content": "Content here",
            "expected_action": "skip",
        })
        ex = EvalExample.model_validate_json(line)
        assert ex.from_sender == "Sender <s@x.com>"
        assert ex.expected_action == "skip"
        assert ex.expected_category is None

    def test_extract_with_category(self):
        """Extract examples can have expected_category and expected_content."""
        data = {
            "from": "Auth <a@b.com>",
            "subject": "Test",
            "content": "body",
            "expected_action": "extract",
            "expected_category": "AI Agents and Tools",
            "expected_content": "Some insight",
        }
        ex = EvalExample.model_validate(data)
        assert ex.expected_category == "AI Agents and Tools"
        assert ex.expected_content == "Some insight"


class TestLLMResponse:
    def test_extract_response(self):
        resp = LLMResponse(
            action="extract",
            category="Politics and Economics",
            content="Key insight here",
            reason="newsletter about policy",
        )
        assert resp.action == "extract"
        assert resp.category == "Politics and Economics"

    def test_skip_response(self):
        resp = LLMResponse(action="skip", reason="job listings")
        assert resp.category is None
        assert resp.content is None


class TestExampleResult:
    def test_defaults(self, sample_extract_example):
        result = ExampleResult(example=sample_extract_example)
        assert result.action_correct is False
        assert result.category_correct is None
        assert result.parse_error is False


class TestRunSummary:
    def test_perfect_score(self):
        summary = RunSummary(
            total=20,
            correct_actions=20,
            correct_categories=6,
            category_comparisons=6,
            extract_accuracy=1.0,
            category_accuracy=1.0,
            score=1.0,
            errors=0,
        )
        assert summary.score == 1.0

    def test_partial_score(self):
        summary = RunSummary(
            total=20,
            correct_actions=16,
            correct_categories=4,
            category_comparisons=6,
            extract_accuracy=0.8,
            category_accuracy=0.6667,
            score=0.7467,
            errors=0,
        )
        assert summary.score == 0.7467
