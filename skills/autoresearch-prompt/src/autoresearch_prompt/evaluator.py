# ABOUTME: Core evaluation logic: load eval set, call LLM, score responses
# ABOUTME: Sequential API calls to Claude haiku, computes 0.6*extract + 0.4*category score

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
    return LLMResponse.model_validate(data)


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
        system, user = load_and_render(
            from_sender=example.from_sender,
            subject=example.subject,
            content=example.content,
            prompt_path=prompt_path,
        )

        start = time.monotonic()
        raw, in_tok, out_tok = call_llm(client, system, user, model)
        result.latency_ms = int((time.monotonic() - start) * 1000)
        result.input_tokens = in_tok
        result.output_tokens = out_tok

        response = parse_llm_output(raw)
        result.response = response
        result.action_correct = response.action.lower() == example.expected_action.lower()

        if example.expected_action == "extract" and response.action.lower() == "extract":
            if example.expected_category and response.category:
                result.category_correct = (
                    response.category.lower() == example.expected_category.lower()
                )
            else:
                result.category_correct = None

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


def compute_score(results: list[ExampleResult]) -> RunSummary:
    """Compute aggregate score from individual results."""
    total = len(results)
    correct_actions = sum(1 for r in results if r.action_correct)
    errors = sum(1 for r in results if r.parse_error)

    # Category accuracy: only count examples where we can compare
    category_comparisons = sum(1 for r in results if r.category_correct is not None)
    correct_categories = sum(1 for r in results if r.category_correct is True)

    extract_accuracy = correct_actions / total if total > 0 else 0.0
    # When no category comparisons possible, treat as 1.0
    category_accuracy = (
        correct_categories / category_comparisons if category_comparisons > 0 else 1.0
    )

    score = 0.6 * extract_accuracy + 0.4 * category_accuracy

    total_input = sum(r.input_tokens for r in results)
    total_output = sum(r.output_tokens for r in results)
    latencies = [r.latency_ms for r in results if r.latency_ms > 0]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    # Estimate cost
    cost = 0.0
    for model_id, (input_price, output_price) in MODEL_PRICING.items():
        # Use first matching model pricing (caller passes model but we don't track it per-result)
        cost = (total_input * input_price + total_output * output_price) / 1_000_000
        break

    return RunSummary(
        total=total,
        correct_actions=correct_actions,
        correct_categories=correct_categories,
        category_comparisons=category_comparisons,
        extract_accuracy=round(extract_accuracy, 4),
        category_accuracy=round(category_accuracy, 4),
        score=round(score, 4),
        errors=errors,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        cost_usd=round(cost, 4),
        avg_latency_ms=avg_latency,
    )


def classify_single(
    from_sender: str,
    subject: str,
    content: str,
    prompt_path: Path | None = None,
    model: str = DEFAULT_MODEL,
) -> LLMResponse:
    """Classify a single newsletter. Returns parsed LLMResponse."""
    client = anthropic.Anthropic()
    system, user = load_and_render(
        from_sender=from_sender,
        subject=subject,
        content=content,
        prompt_path=prompt_path,
    )
    raw, _, _ = call_llm(client, system, user, model)
    return parse_llm_output(raw)


def run_evaluation(
    prompt_path: Path | None = None,
    eval_path: Path | None = None,
    model: str = DEFAULT_MODEL,
) -> RunSummary:
    """Run full evaluation: load examples, call LLM, compute score."""
    client = anthropic.Anthropic()
    examples = load_eval_set(eval_path)

    results: list[ExampleResult] = []
    for i, example in enumerate(examples):
        print(f"  [{i + 1}/{len(examples)}] {example.subject[:60]}...", file=sys.stderr)
        result = evaluate_example(client, example, prompt_path, model)
        results.append(result)

        if result.parse_error:
            print(f"    ERROR: {result.error_message}", file=sys.stderr)
        elif not result.action_correct:
            expected = example.expected_action
            got = result.response.action if result.response else "none"
            print(f"    WRONG action: expected={expected} got={got}", file=sys.stderr)

    return compute_score(results)
