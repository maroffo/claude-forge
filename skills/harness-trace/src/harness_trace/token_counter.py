# ABOUTME: Token counting and baselining for claude-forge harness files
# ABOUTME: Uses tiktoken for exact token counts, generates TSV baselines

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import tiktoken

# Claude uses cl100k_base tokenizer (same family as GPT-4 / Claude)
ENCODING_NAME = "cl100k_base"


@dataclass
class FileTokenCount:
    file: str
    tokens: int
    words: int
    lines: int
    tier: str  # rule, skill, skill-ref, agent
    loaded: str  # always, on-demand


def _get_encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(ENCODING_NAME)


def count_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding."""
    enc = _get_encoding()
    return len(enc.encode(text))


def count_file_tokens(path: Path) -> int:
    """Count tokens in a file."""
    text = path.read_text(encoding="utf-8")
    return count_tokens(text)


def _classify_file(path: Path, base_dir: Path) -> tuple[str, str]:
    """Classify a file into tier and loaded status.

    Returns (tier, loaded) tuple.
    """
    try:
        relative = path.relative_to(base_dir)
    except ValueError:
        return ("unknown", "unknown")

    parts = relative.parts

    if len(parts) >= 1 and parts[0] == "rules":
        return ("rule", "always")

    if len(parts) >= 1 and parts[0] == "agents":
        return ("agent", "on-demand")

    if len(parts) >= 1 and parts[0] == "skills":
        # Reference files at top level of skills/
        if len(parts) == 2 and parts[1].startswith("_"):
            return ("skill-ref", "on-demand")
        # Files in references/ subdirectory
        if "references" in parts:
            return ("skill-ref", "on-demand")
        return ("skill", "on-demand")

    # CLAUDE.md at root
    if path.name in ("CLAUDE.md", "CLAUDE.md.example"):
        return ("config", "always")

    return ("other", "unknown")


def scan_directory(
    directory: Path,
    base_dir: Path | None = None,
) -> list[FileTokenCount]:
    """Scan a directory for markdown files and count tokens.

    Args:
        directory: Directory to scan.
        base_dir: Base directory for classification. If None, uses directory's parent
                  or the directory itself.
    """
    if base_dir is None:
        # Heuristic: if directory is rules/, skills/, or agents/, parent is base
        if directory.name in ("rules", "skills", "agents"):
            base_dir = directory.parent
        else:
            base_dir = directory

    results: list[FileTokenCount] = []
    extensions = {".md", ".py"}

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        # Skip hidden files and __pycache__
        if any(p.startswith(".") or p == "__pycache__" for p in path.parts):
            continue
        # Skip test files
        if "tests" in path.parts or "test_" in path.name:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        tier, loaded = _classify_file(path, base_dir)
        results.append(FileTokenCount(
            file=str(path.relative_to(base_dir)),
            tokens=count_tokens(text),
            words=len(text.split()),
            lines=text.count("\n") + (1 if text and not text.endswith("\n") else 0),
            tier=tier,
            loaded=loaded,
        ))

    return results


def generate_baseline_tsv(results: list[FileTokenCount]) -> str:
    """Generate a TSV baseline report from token counts."""
    lines = ["file\ttokens\twords\tlines\ttier\tloaded"]
    for r in sorted(results, key=lambda x: (-x.tokens, x.file)):
        lines.append(f"{r.file}\t{r.tokens}\t{r.words}\t{r.lines}\t{r.tier}\t{r.loaded}")

    # Summary
    always_on = sum(r.tokens for r in results if r.loaded == "always")
    on_demand = sum(r.tokens for r in results if r.loaded == "on-demand")
    total = sum(r.tokens for r in results)

    lines.append("")
    lines.append(f"# Always-on: {always_on} tokens")
    lines.append(f"# On-demand: {on_demand} tokens")
    lines.append(f"# Total: {total} tokens")

    # Top 5 by tier
    for tier in ("rule", "skill", "agent"):
        tier_items = sorted(
            [r for r in results if r.tier == tier],
            key=lambda x: -x.tokens,
        )[:5]
        if tier_items:
            lines.append(f"# Top 5 {tier}s: " + ", ".join(
                f"{r.file} ({r.tokens})" for r in tier_items
            ))

    return "\n".join(lines) + "\n"


def print_token_counts(results: list[FileTokenCount], output: object = sys.stdout) -> None:
    """Print token counts in a human-readable format."""
    write = getattr(output, "write", print)
    total = 0
    for r in sorted(results, key=lambda x: (-x.tokens, x.file)):
        write(f"{r.tokens:>6}  {r.file}\n")
        total += r.tokens
    write(f"\n{'─' * 40}\n")
    write(f"{total:>6}  TOTAL\n")
