# ABOUTME: Tests for Pydantic models: dynamic field splitting, validation
# ABOUTME: Covers EvalExample model_validator, LLMResponse fields, ExampleResult, RunSummary

from __future__ import annotations

import json

from autoresearch_prompt.models import EvalExample, ExampleResult, LLMResponse, RunSummary


class TestEvalExample:
    def test_splits_expected_prefix(self):
        """Fields with expected_ prefix go to expected dict, rest to inputs."""
        data = {
            "from": "Author <a@b.com>",
            "subject": "Test",
            "content": "body",
            "expected_action": "extract",
            "expected_category": "AI Agents and Tools",
        }
        ex = EvalExample.model_validate(data)
        assert ex.inputs == {"from": "Author <a@b.com>", "subject": "Test", "content": "body"}
        assert ex.expected == {"action": "extract", "category": "AI Agents and Tools"}

    def test_from_jsonl_line(self):
        """Parse a JSONL line with expected_ prefix splitting."""
        line = json.dumps(
            {
                "from": "Sender <s@x.com>",
                "subject": "Sub",
                "content": "Content here",
                "expected_action": "skip",
            }
        )
        ex = EvalExample.model_validate_json(line)
        assert ex.inputs["from"] == "Sender <s@x.com>"
        assert ex.expected["action"] == "skip"
        assert "category" not in ex.expected

    def test_extract_with_all_expected_fields(self):
        """Extract examples can have multiple expected_ fields."""
        data = {
            "from": "Auth <a@b.com>",
            "subject": "Test",
            "content": "body",
            "expected_action": "extract",
            "expected_category": "AI Agents and Tools",
            "expected_content": "Some insight",
        }
        ex = EvalExample.model_validate(data)
        assert ex.expected["category"] == "AI Agents and Tools"
        assert ex.expected["content"] == "Some insight"

    def test_passthrough_when_inputs_already_present(self):
        """If data already has inputs/expected structure, pass through."""
        data = {
            "inputs": {"text": "hello"},
            "expected": {"label": "greeting"},
        }
        ex = EvalExample.model_validate(data)
        assert ex.inputs == {"text": "hello"}
        assert ex.expected == {"label": "greeting"}

    def test_non_newsletter_schema(self):
        """Arbitrary input/expected fields work (commit messages, etc.)."""
        data = {
            "diff": "- old\n+ new",
            "context": "refactor",
            "expected_message": "Refactor: simplify logic",
        }
        ex = EvalExample.model_validate(data)
        assert ex.inputs == {"diff": "- old\n+ new", "context": "refactor"}
        assert ex.expected == {"message": "Refactor: simplify logic"}


class TestLLMResponse:
    def test_from_dict(self):
        resp = LLMResponse(
            fields={
                "action": "extract",
                "category": "Politics and Economics",
                "content": "Key insight here",
                "reason": "newsletter about policy",
            }
        )
        assert resp.fields["action"] == "extract"
        assert resp.fields["category"] == "Politics and Economics"

    def test_minimal_fields(self):
        resp = LLMResponse(fields={"action": "skip", "reason": "job listings"})
        assert "category" not in resp.fields


class TestExampleResult:
    def test_defaults(self):
        ex = EvalExample.model_validate(
            {
                "from": "a",
                "subject": "s",
                "content": "c",
                "expected_action": "extract",
            }
        )
        result = ExampleResult(example=ex)
        assert result.field_correct == {}
        assert result.parse_error is False

    def test_field_correct_dict(self):
        ex = EvalExample.model_validate(
            {
                "from": "a",
                "subject": "s",
                "content": "c",
                "expected_action": "extract",
                "expected_category": "Dev",
            }
        )
        result = ExampleResult(
            example=ex,
            field_correct={"action": True, "category": False},
        )
        assert result.field_correct["action"] is True
        assert result.field_correct["category"] is False


class TestRunSummary:
    def test_with_field_accuracies(self):
        summary = RunSummary(
            total=20,
            field_accuracies={"action": 1.0, "category": 1.0},
            score=1.0,
            errors=0,
        )
        assert summary.score == 1.0
        assert summary.field_accuracies["action"] == 1.0

    def test_partial_score(self):
        summary = RunSummary(
            total=20,
            field_accuracies={"action": 0.8, "category": 0.6667},
            score=0.7467,
            errors=0,
        )
        assert summary.score == 0.7467
        assert summary.field_accuracies["category"] == 0.6667
