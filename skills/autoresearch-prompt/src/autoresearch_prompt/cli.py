# ABOUTME: CLI entry point with evaluate subcommand
# ABOUTME: Outputs score/accuracy/cost in grep-friendly format

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evaluator import DEFAULT_MODEL, run_evaluation


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="autoresearch-prompt",
        description="Autonomous prompt optimization eval harness",
    )
    sub = parser.add_subparsers(dest="command", required=True)

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
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )

    return parser.parse_args(argv)


def _cmd_evaluate(args: argparse.Namespace) -> None:
    print("Running evaluation...", file=sys.stderr)
    summary = run_evaluation(
        prompt_path=args.prompt,
        eval_path=args.eval_set,
        model=args.model,
    )

    # Stdout: grep-friendly key-value format
    print(f"score: {summary.score:.2f}")
    print(f"extract_acc: {summary.extract_accuracy:.2f}")
    print(f"category_acc: {summary.category_accuracy:.2f}")
    print(f"cost: ${summary.cost_usd:.4f}")
    print(f"latency_ms: {summary.avg_latency_ms}")
    print(f"errors: {summary.errors}")
    print(f"total: {summary.total}")


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "evaluate":
        _cmd_evaluate(args)
