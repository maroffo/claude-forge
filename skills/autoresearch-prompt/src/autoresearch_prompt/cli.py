# ABOUTME: CLI entry point with evaluate and classify subcommands
# ABOUTME: evaluate scores prompt with --weights; classify takes stdin JSON input fields

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import get_default_model
from .evaluator import classify_single, run_evaluation


def _parse_weights(raw: str) -> dict[str, float]:
    """Parse 'field=0.6,field2=0.4' into dict."""
    weights: dict[str, float] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        key, val = pair.split("=")
        weights[key.strip()] = float(val.strip())
    return weights


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    default_model = get_default_model()

    parser = argparse.ArgumentParser(
        prog="autoresearch-prompt",
        description="Autonomous prompt optimization eval harness",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # evaluate
    eval_parser = sub.add_parser("evaluate", help="Run prompt against eval set")
    eval_parser.add_argument(
        "--prompt",
        type=Path,
        default=None,
        help="Path to prompt.md (default: bundled prompt.md)",
    )
    eval_parser.add_argument(
        "--eval-set",
        type=Path,
        default=None,
        help="Path to eval_set.jsonl (default: bundled eval_set.jsonl)",
    )
    eval_parser.add_argument(
        "--model",
        type=str,
        default=default_model,
        help=f"Model to use (default: {default_model})",
    )
    eval_parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Field weights: action=0.6,category=0.4 (default: equal weight)",
    )

    # classify
    cls_parser = sub.add_parser(
        "classify",
        help="Classify a single input (stdin JSON)",
    )
    cls_parser.add_argument(
        "--prompt",
        type=Path,
        default=None,
        help="Path to prompt.md (default: bundled prompt.md)",
    )
    cls_parser.add_argument(
        "--model",
        type=str,
        default=default_model,
        help=f"Model to use (default: {default_model})",
    )

    return parser.parse_args(argv)


def _cmd_evaluate(args: argparse.Namespace) -> None:
    weights = _parse_weights(args.weights) if args.weights else None

    print("Running evaluation...", file=sys.stderr)
    summary = run_evaluation(
        prompt_path=args.prompt,
        eval_path=args.eval_set,
        model=args.model,
        weights=weights,
    )

    # Stdout: grep-friendly key-value format
    print(f"score: {summary.score:.2f}")
    show_fields = weights.keys() if weights else summary.field_accuracies.keys()
    for field in sorted(show_fields):
        acc = summary.field_accuracies.get(field, 0.0)
        print(f"{field}_acc: {acc:.2f}")
    print(f"cost: ${summary.cost_usd:.4f}")
    print(f"latency_ms: {summary.avg_latency_ms}")
    print(f"errors: {summary.errors}")
    print(f"total: {summary.total}")


def _cmd_classify(args: argparse.Namespace) -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        print("Pipe JSON to stdin.", file=sys.stderr)
        sys.exit(1)
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(fields, dict):
        print("Expected a JSON object, not an array or scalar.", file=sys.stderr)
        sys.exit(1)

    response = classify_single(
        fields=fields,
        prompt_path=args.prompt,
        model=args.model,
    )
    print(json.dumps(response.fields, indent=2))


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "evaluate":
        _cmd_evaluate(args)
    elif args.command == "classify":
        _cmd_classify(args)
