# ABOUTME: Pydantic models for eval examples, LLM responses, and run summaries
# ABOUTME: Dynamic dict-based fields: inputs/expected from JSONL, fields from LLM output

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class EvalExample(BaseModel):
    """A single labeled example from eval_set.jsonl.

    Convention: keys starting with ``expected_`` become ``expected`` (prefix stripped),
    everything else becomes ``inputs``. No schema config needed.
    """

    inputs: dict[str, str]
    expected: dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def split_fields(cls, data: Any) -> Any:
        if isinstance(data, dict) and "inputs" not in data:
            inputs: dict[str, str] = {}
            expected: dict[str, str] = {}
            for key, value in data.items():
                if key.startswith("expected_"):
                    expected[key.removeprefix("expected_")] = value
                else:
                    inputs[key] = value
            return {"inputs": inputs, "expected": expected}
        return data


class LLMResponse(BaseModel):
    """Parsed JSON output from the LLM."""

    fields: dict[str, Any]


class ExampleResult(BaseModel):
    """Result of evaluating a single example."""

    example: EvalExample
    response: LLMResponse | None = None
    field_correct: dict[str, bool] = {}
    parse_error: bool = False
    error_message: str | None = None
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class RunSummary(BaseModel):
    """Aggregate results of a full evaluation run."""

    total: int
    field_accuracies: dict[str, float]
    score: float
    errors: int
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cost_usd: float = 0.0
    avg_latency_ms: int = 0
