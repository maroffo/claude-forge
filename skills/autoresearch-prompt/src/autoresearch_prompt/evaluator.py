# ABOUTME: Core evaluation logic: load eval set, call LLM, score responses
# ABOUTME: Generic field comparison with configurable weights via dict

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import anthropic

from .models import EvalExample, ExampleResult, LLMResponse, RunSummary
from .prompt_loader import load_and_render

EVAL_SET_PATH = Path(__file__).resolve().parent.parent.parent / "eval_set.jsonl"

# Hardcoded pricing per 1M tokens (USD) - informational only
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-5-20250514": (3.00, 15.00),
}

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", re.DOTALL)


def load_eval_set(path: Path | None = None) -> list[EvalExample]:
    """Load evaluation examples from JSONL file."""
    p = path or EVAL_SET_PATH
    examples = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        examples.append(EvalExample.model_validate_json(line))
    return examples


def _strip_fences(text: str) -> str:
    """Remove markdown code fences wrapping JSON."""
    text = text.strip()
    match = _FENCE_RE.match(text)
    if match:
        return match.group(1).strip()
    return text


def parse_llm_output(raw: str) -> LLMResponse:
    """Parse LLM text output into structured LLMResponse."""
    cleaned = _strip_fences(raw)
    data = json.loads(cleaned)
    return LLMResponse(fields=data)


def call_llm(
    client: anthropic.Anthropic,
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
) -> tuple[str, int, int]:
    """Call Claude API. Returns (response_text, input_tokens, output_tokens)."""
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = response.content[0].text
    return text, response.usage.input_tokens, response.usage.output_tokens


def evaluate_example(
    client: anthropic.Anthropic,
    example: EvalExample,
    prompt_path: Path | None = None,
    model: str = DEFAULT_MODEL,
) -> ExampleResult:
    """Evaluate a single example against the prompt."""
    result = ExampleResult(example=example)

    try:
        system, user = load_and_render(example.inputs, prompt_path=prompt_path)

        start = time.monotonic()
        raw, in_tok, out_tok = call_llm(client, system, user, model)
        result.latency_ms = int((time.monotonic() - start) * 1000)
        result.input_tokens = in_tok
        result.output_tokens = out_tok

        response = parse_llm_output(raw)
        result.response = response

        # Compare each expected field against the response
        field_correct: dict[str, bool] = {}
        for field, expected_val in example.expected.items():
            actual_val = response.fields.get(field)
            if actual_val is not None:
                field_correct[field] = (
                    str(actual_val).strip().lower() == expected_val.strip().lower()
                )
            else:
                field_correct[field] = False
        result.field_correct = field_correct

    except json.JSONDecodeError as e:
        result.parse_error = True
        result.error_message = f"JSON parse error: {e}"
    except anthropic.APIError as e:
        result.parse_error = True
        result.error_message = f"API error: {e}"
    except Exception as e:
        result.parse_error = True
        result.error_message = f"Unexpected error: {e}"

    return result


def compute_score(
    results: list[ExampleResult],
    weights: dict[str, float] | None = None,
) -> RunSummary:
    """Compute aggregate score from individual results.

    *weights*: ``{"action": 0.6, "category": 0.4}`` scores only those fields
    with the given weights. ``None`` means equal weight across all expected fields.
    """
    total = len(results)
    errors = sum(1 for r in results if r.parse_error)

    # Collect all expected field names across examples
    all_fields: set[str] = set()
    for r in results:
        all_fields.update(r.example.expected.keys())

    # Per-field accuracy: correct / comparisons (skip examples that don't have the field)
    field_accuracies: dict[str, float] = {}
    for field in sorted(all_fields):
        comparisons = sum(1 for r in results if field in r.field_correct)
        correct = sum(1 for r in results if r.field_correct.get(field) is True)
        field_accuracies[field] = round(correct / comparisons, 4) if comparisons > 0 else 1.0

    # Weighted score
    if weights:
        scored_fields = {f: w for f, w in weights.items() if f in field_accuracies}
    else:
        scored_fields = {f: 1.0 for f in field_accuracies}

    weight_sum = sum(scored_fields.values())
    if weight_sum > 0:
        score = sum(
            field_accuracies.get(f, 1.0) * w for f, w in scored_fields.items()
        ) / weight_sum
    else:
        score = 0.0

    total_input = sum(r.input_tokens for r in results)
    total_output = sum(r.output_tokens for r in results)
    latencies = [r.latency_ms for r in results if r.latency_ms > 0]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    # Estimate cost
    cost = 0.0
    for _model_id, (input_price, output_price) in MODEL_PRICING.items():
        cost = (total_input * input_price + total_output * output_price) / 1_000_000
        break

    return RunSummary(
        total=total,
        field_accuracies=field_accuracies,
        score=round(score, 4),
        errors=errors,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        cost_usd=round(cost, 4),
        avg_latency_ms=avg_latency,
    )


def classify_single(
    fields: dict[str, str],
    prompt_path: Path | None = None,
    model: str = DEFAULT_MODEL,
) -> LLMResponse:
    """Classify a single input. Returns parsed LLMResponse."""
    client = anthropic.Anthropic()
    system, user = load_and_render(fields, prompt_path=prompt_path)
    raw, _, _ = call_llm(client, system, user, model)
    return parse_llm_output(raw)


def run_evaluation(
    prompt_path: Path | None = None,
    eval_path: Path | None = None,
    model: str = DEFAULT_MODEL,
    weights: dict[str, float] | None = None,
) -> RunSummary:
    """Run full evaluation: load examples, call LLM, compute score."""
    client = anthropic.Anthropic()
    examples = load_eval_set(eval_path)

    # Use first input field as progress label
    label_key = next(iter(examples[0].inputs), "input") if examples else "input"

    results: list[ExampleResult] = []
    for i, example in enumerate(examples):
        label = str(example.inputs.get(label_key, ""))[:60]
        print(f"  [{i + 1}/{len(examples)}] {label}...", file=sys.stderr)
        result = evaluate_example(client, example, prompt_path, model)
        results.append(result)

        if result.parse_error:
            print(f"    ERROR: {result.error_message}", file=sys.stderr)
        elif not all(result.field_correct.values()):
            wrong = [f for f, v in result.field_correct.items() if not v]
            print(f"    WRONG fields: {', '.join(wrong)}", file=sys.stderr)

    return compute_score(results, weights)
