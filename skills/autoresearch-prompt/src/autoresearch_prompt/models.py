# ABOUTME: Pydantic models for eval examples, LLM responses, and run summaries
# ABOUTME: EvalExample (JSONL row), LLMResponse (parsed output), ExampleResult, RunSummary

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvalExample(BaseModel):
    """A single labeled example from eval_set.jsonl."""

    model_config = ConfigDict(populate_by_name=True)

    from_sender: str = Field(alias="from")
    subject: str
    content: str
    expected_action: str  # "extract" or "skip"
    expected_category: str | None = None  # only for action=extract
    expected_content: str | None = None  # brief description of expected extraction


class LLMResponse(BaseModel):
    """Parsed JSON output from the LLM."""

    action: str  # "extract" or "skip"
    category: str | None = None
    content: str | None = None
    reason: str | None = None


class ExampleResult(BaseModel):
    """Result of evaluating a single example."""

    example: EvalExample
    response: LLMResponse | None = None
    action_correct: bool = False
    category_correct: bool | None = None  # None if action=skip
    parse_error: bool = False
    error_message: str | None = None
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class RunSummary(BaseModel):
    """Aggregate results of a full evaluation run."""

    total: int
    correct_actions: int
    correct_categories: int
    category_comparisons: int  # how many had both expected and actual category
    extract_accuracy: float
    category_accuracy: float
    score: float  # 0.6 * extract_acc + 0.4 * category_acc
    errors: int
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cost_usd: float = 0.0
    avg_latency_ms: int = 0
