# ABOUTME: CLI entry point for harness-trace tool
# ABOUTME: Subcommands: extract (session JSONL -> traces), count-tokens, baseline

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


def _cmd_extract(args: argparse.Namespace) -> None:
    """Extract structured traces from a session JSONL file."""
    from harness_trace.extractor import extract_traces, write_traces

    session_path = Path(args.session)
    if not session_path.exists():
        print(f"Error: session file not found: {session_path}", file=sys.stderr)
        sys.exit(1)

    slug = args.slug or session_path.stem
    entries = extract_traces(session_path, session_slug=slug)

    if not entries:
        print("No orchestrator steps detected in session.", file=sys.stderr)
        sys.exit(0)

    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        output_path = output_dir / f"{date_str}_{slug}.jsonl"
        write_traces(entries, output_path)
        print(f"Wrote {len(entries)} trace entries to {output_path}", file=sys.stderr)
    else:
        for entry in entries:
            print(entry.to_jsonl())


def _cmd_count_tokens(args: argparse.Namespace) -> None:
    """Count tokens in harness files."""
    from harness_trace.token_counter import print_token_counts, scan_directory

    target = Path(args.path)
    if not target.exists():
        print(f"Error: path not found: {target}", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(args.base_dir) if args.base_dir else None
    if target.is_file():
        from harness_trace.token_counter import count_file_tokens

        tokens = count_file_tokens(target)
        print(f"{tokens:>6}  {target}")
    else:
        results = scan_directory(target, base_dir=base_dir)
        print_token_counts(results)


def _cmd_baseline(args: argparse.Namespace) -> None:
    """Generate a full token baseline for the harness."""
    from harness_trace.token_counter import generate_baseline_tsv, scan_directory

    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"Error: base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    all_results = []
    for subdir in ("rules", "skills", "agents"):
        path = base_dir / subdir
        if path.exists():
            all_results.extend(scan_directory(path, base_dir=base_dir))

    # Also scan CLAUDE.md if present
    for name in ("CLAUDE.md", "CLAUDE.md.example"):
        claude_md = base_dir / name
        if claude_md.exists():
            from harness_trace.token_counter import FileTokenCount, count_tokens

            text = claude_md.read_text(encoding="utf-8")
            all_results.append(FileTokenCount(
                file=name,
                tokens=count_tokens(text),
                words=len(text.split()),
                lines=text.count("\n") + 1,
                tier="config",
                loaded="always",
            ))

    tsv = generate_baseline_tsv(all_results)

    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        output_path = output_dir / f"{date_str}_baseline.tsv"
        output_path.write_text(tsv, encoding="utf-8")
        print(f"Wrote baseline to {output_path}", file=sys.stderr)
    else:
        print(tsv)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="harness-trace",
        description="Structured execution trace capture and token baselining for claude-forge",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = subparsers.add_parser(
        "extract",
        help="Extract structured traces from a session JSONL file",
    )
    p_extract.add_argument("session", help="Path to session JSONL file")
    p_extract.add_argument("--slug", help="Session slug (default: filename stem)")
    p_extract.add_argument(
        "--output", "-o",
        help="Output directory (default: stdout)",
    )

    # count-tokens
    p_count = subparsers.add_parser(
        "count-tokens",
        help="Count tokens in harness files",
    )
    p_count.add_argument("path", help="File or directory to count")
    p_count.add_argument(
        "--base-dir",
        help="Base directory for tier classification",
    )

    # baseline
    p_baseline = subparsers.add_parser(
        "baseline",
        help="Generate full token baseline for the harness",
    )
    p_baseline.add_argument(
        "--base-dir",
        default=".",
        help="Root directory containing rules/, skills/, agents/ (default: .)",
    )
    p_baseline.add_argument(
        "--output", "-o",
        help="Output directory for TSV file (default: stdout)",
    )

    args = parser.parse_args()

    commands = {
        "extract": _cmd_extract,
        "count-tokens": _cmd_count_tokens,
        "baseline": _cmd_baseline,
    }
    commands[args.command](args)
