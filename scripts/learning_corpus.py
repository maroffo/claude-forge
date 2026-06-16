#!/usr/bin/env python3
# ABOUTME: Ingest LEARNING.md retrospectives across repos into a normalized atomic-learning corpus
# ABOUTME: Deterministic phase 1 of the cross-repo learning loop; recurrence detection is a separate agent pass

"""Build a normalized corpus of atomic learnings from LEARNING.md files.

Each LEARNING.md follows a stable shape: a `## Lessons Learned` (and optionally
`## Pitfalls & Gotchas` / `## Best Practices Discovered`) section whose entries are
`### [YYYY-MM-DD: ]Title` blocks. This script discovers those files under a root,
drops duplicate working copies (temp/, fix/, backups), splits each into atomic
learnings, and emits one JSON object per learning to a JSONL corpus.

No LLM, no network: this is the reproducible substrate the recurrence pass reads.

Usage:
    uv run scripts/learning_corpus.py --root ~/Development --out corpus.jsonl
    uv run scripts/learning_corpus.py --root ~/Development --stats
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# Section headings whose ### entries are atomic learnings worth harvesting.
# Anything else (Project Overview, Architecture, Tech Stack) is project context, not a lesson.
HARVEST_SECTIONS = {
    "lessons learned",
    "pitfalls & gotchas",
    "pitfalls and gotchas",
    "best practices discovered",
    "best practices",
}

# Path segments that mark a non-canonical working copy of a repo we'd otherwise
# count twice. Keeps recurrence counts honest (a temp clone is not a second repo).
DUP_SEGMENTS = ("/temp/", "/fix/", "/backup/", "/.backup/", "/copy/")

# Optional leading date in any of the shapes seen across repos:
#   ### 2026-02-17: Title        ### 2026-05-19 · Title        ### 2026-06-10/11 — Title
#   ### 2026-04-15 (evening): Title
# Captures the base date only; a /DD range suffix and a parenthetical qualifier are consumed but dropped.
ENTRY_RE = re.compile(
    r"^### +(?:(\d{4}-\d{2}-\d{2})(?:/\d{1,2})?\s*(?:\([^)]*\))?\s*[:\-\|–—·]\s*)?(.+?)\s*$"
)
SECTION_RE = re.compile(r"^## +(.+?)\s*$")
ABOUTME_RE = re.compile(r"^#\s*ABOUTME:", re.IGNORECASE)


def find_learning_files(root: Path) -> list[Path]:
    """All LEARNING.md under root, excluding VCS/deps and duplicate working copies."""
    files = []
    for p in root.rglob("LEARNING.md"):
        parts = str(p)
        if "/node_modules/" in parts or "/.git/" in parts or "/.venv/" in parts:
            continue
        if any(seg in parts for seg in DUP_SEGMENTS):
            continue
        files.append(p)
    return sorted(files)


def repo_name(path: Path, root: Path) -> str:
    """Repo identity = the path of the dir holding LEARNING.md, relative to root."""
    rel = path.parent.relative_to(root) if path.parent != root else path.parent
    return str(rel)


def parse_file(path: Path, root: Path) -> list[dict]:
    """Split one LEARNING.md into atomic learnings under harvested sections."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    learnings: list[dict] = []
    current_section: str | None = None
    in_harvest = False
    entry: dict | None = None
    body: list[str] = []

    def flush() -> None:
        nonlocal entry, body
        if entry is not None:
            content = "\n".join(body).strip()
            entry["body"] = content
            entry["body_lines"] = len(content.splitlines()) if content else 0
            learnings.append(entry)
        entry = None
        body = []

    for line in lines:
        if ABOUTME_RE.match(line):
            continue

        sec = SECTION_RE.match(line)
        if sec:
            flush()
            current_section = sec.group(1).strip()
            in_harvest = current_section.lower() in HARVEST_SECTIONS
            continue

        if in_harvest:
            m = ENTRY_RE.match(line)
            if m:
                flush()
                entry = {
                    "repo": repo_name(path, root),
                    "source": str(path),
                    "section": current_section,
                    "date": m.group(1),  # may be None
                    "title": m.group(2).strip(),
                }
                continue
            if entry is not None:
                body.append(line)

    flush()
    return learnings


def build_corpus(root: Path) -> tuple[list[dict], list[Path]]:
    files = find_learning_files(root)
    corpus: list[dict] = []
    for f in files:
        corpus.extend(parse_file(f, root))
    return corpus, files


def print_stats(corpus: list[dict], files: list[Path], root: Path) -> None:
    by_repo: dict[str, int] = {}
    by_section: dict[str, int] = {}
    undated = 0
    for c in corpus:
        by_repo[c["repo"]] = by_repo.get(c["repo"], 0) + 1
        sect = (c["section"] or "?").strip()
        by_section[sect] = by_section.get(sect, 0) + 1
        if not c["date"]:
            undated += 1

    print(f"Scanned root: {root}")
    print(f"LEARNING.md files (canonical): {len(files)}")
    print(f"Atomic learnings: {len(corpus)}  ({undated} undated)")
    print()
    print("By repo:")
    for repo, n in sorted(by_repo.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:4d}  {repo}")
    print()
    print("By section:")
    for sect, n in sorted(by_section.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {sect}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path.home() / "Development",
                    help="Directory to scan recursively for LEARNING.md (default: ~/Development)")
    ap.add_argument("--out", type=Path, default=None,
                    help="Write JSONL corpus to this path (one learning per line)")
    ap.add_argument("--stats", action="store_true",
                    help="Print a coverage summary to stdout")
    args = ap.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    corpus, files = build_corpus(root)
    if not corpus:
        print(f"warning: no atomic learnings found under {root}", file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as fh:
            for c in corpus:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"Wrote {len(corpus)} learnings from {len(files)} files to {args.out}")

    if args.stats or not args.out:
        print_stats(corpus, files, root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
