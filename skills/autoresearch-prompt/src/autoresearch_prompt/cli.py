# ABOUTME: CLI entry point with evaluate and classify subcommands
# ABOUTME: evaluate scores prompt against eval set; classify triages a single newsletter

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluator import DEFAULT_MODEL, classify_single, run_evaluation


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )

    # classify
    cls_parser = sub.add_parser(
        "classify", help="Classify a single newsletter (stdin JSON or args)",
    )
    cls_parser.add_argument("--from", dest="from_sender", help="Sender (From header)")
    cls_parser.add_argument("--subject", help="Email subject")
    cls_parser.add_argument("--content", help="Email body text")
    cls_parser.add_argument(
        "--prompt",
        type=Path,
        default=None,
        help="Path to prompt.md (default: bundled prompt.md)",
    )
    cls_parser.add_argument(
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


def _cmd_classify(args: argparse.Namespace) -> None:
    # Read from args or stdin JSON
    if args.from_sender and args.subject and args.content:
        from_sender = args.from_sender
        subject = args.subject
        content = args.content
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            print("Provide --from/--subject/--content or pipe JSON to stdin.", file=sys.stderr)
            sys.exit(1)
        data = json.loads(raw)
        from_sender = data.get("from", data.get("from_sender", ""))
        subject = data.get("subject", "")
        content = data.get("content", "")

    response = classify_single(
        from_sender=from_sender,
        subject=subject,
        content=content,
        prompt_path=args.prompt,
        model=args.model,
    )
    print(response.model_dump_json(indent=2))


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "evaluate":
        _cmd_evaluate(args)
    elif args.command == "classify":
        _cmd_classify(args)
