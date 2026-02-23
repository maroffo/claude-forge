# ABOUTME: CLI entry point with classify and archive subcommands
# ABOUTME: classify reads gog JSON from stdin, archive reads saved state and outputs gog commands

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .classifier import classify_all, load_rules, load_state, save_state
from .formatter import format_archive_commands, format_summary
from .models import GogSearchResult

RULES_PATH = Path(__file__).resolve().parent.parent.parent / "rules.yaml"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="inbox-triage",
        description="Gmail inbox triage: classify and archive by priority",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # classify
    classify_parser = sub.add_parser("classify", help="Classify threads from stdin JSON")
    classify_parser.add_argument(
        "--rules",
        type=Path,
        default=RULES_PATH,
        help=f"Path to rules.yaml (default: {RULES_PATH})",
    )
    classify_parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help="Path to save state file (default: /tmp/inbox-triage-state.json)",
    )

    # archive
    archive_parser = sub.add_parser("archive", help="Archive threads by priority")
    archive_parser.add_argument(
        "priorities",
        nargs="+",
        type=str,
        help="Priorities to archive (e.g. p3 p4)",
    )
    archive_parser.add_argument(
        "--yes",
        action="store_true",
        help="Execute gog commands (without this, only prints them)",
    )
    archive_parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help="Path to state file (default: /tmp/inbox-triage-state.json)",
    )

    return parser.parse_args(argv)


def _cmd_classify(args: argparse.Namespace) -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        print("No input on stdin.", file=sys.stderr)
        sys.exit(1)

    result = GogSearchResult.model_validate_json(raw)
    rules = load_rules(args.rules)
    classified = classify_all(result.threads, rules)
    state_path = save_state(classified, args.state)

    print(format_summary(classified))
    print(f"\nState saved to {state_path}", file=sys.stderr)


def _cmd_archive(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    priorities = [p.upper() for p in args.priorities]
    commands = format_archive_commands(state, priorities)

    if not commands:
        print("No threads to archive for the given priorities.")
        return

    print(f"Archiving {len(commands)} thread(s):\n")

    for tid, cmd in commands:
        if args.yes:
            print(f"  Archiving {tid}...")
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  FAILED: {result.stderr.strip()}", file=sys.stderr)
            else:
                print(f"  OK: {tid}")
        else:
            print(f"  {cmd}")

    if not args.yes:
        print("\nDry run. Add --yes to execute.")


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "classify":
        _cmd_classify(args)
    elif args.command == "archive":
        _cmd_archive(args)
