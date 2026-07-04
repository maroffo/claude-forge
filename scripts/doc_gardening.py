#!/usr/bin/env python3
# ABOUTME: Detect stale cross-references in the harness governance docs (rules, agents, skills, CLAUDE.md)
# ABOUTME: Deterministic phase 1 of the doc-gardening pass; judgment calls are a separate agent pass

"""Find dead references in the docs that steer the harness.

Two deterministic checks, zero LLM:

1. Dead paths: backtick-quoted repo paths (rules/..., skills/..., hooks/...,
   agents/..., scripts/..., docs/...) mentioned in governance docs that do not
   exist on disk.
2. Skill-table drift: skill names referenced in backticks by CLAUDE.md.example
   that have no matching skills/<name>/ directory, and skill directories never
   mentioned anywhere in CLAUDE.md.example (invisible to routing).

Output: one line per finding, `file:line  KIND  token`. Exit 1 if any findings,
0 if clean, so it can gate CI later if it earns it. The agent pass (see the
learning-loop skill) handles the judgment half: claims contradicted by newer
change contracts, rules that describe behavior the code no longer has.

Usage:
    uv run --no-project python3 scripts/doc_gardening.py [--root <repo>]
"""

import argparse
import re
import sys
from pathlib import Path

GOVERNANCE_GLOBS = (
    "CLAUDE.md.example",
    "README.md",
    "rules/*.md",
    "agents/*/*.md",
    "agents/*.md",
    "skills/*/SKILL.md",
)

# Backticked tokens that look like repo paths. Anchored to known top-level dirs
# to keep false positives near zero (a bare `settings.json` or `make check` is
# not checkable; `rules/quality-gates.md` is).
PATH_RE = re.compile(
    r"`((?:rules|agents|hooks|skills|scripts|docs|quality_reports)/[A-Za-z0-9_./\-]+?)`"
)
# Backticked lowercase tokens (skill names are single words or kebab-case).
BACKTICK_TOKEN_RE = re.compile(r"`([a-z][a-z0-9-]*)`")

# Paths that are described as created-on-demand rather than shipped.
ON_DEMAND_PREFIXES = ("quality_reports/", "docs/")


def iter_governance_files(root):
    for pattern in GOVERNANCE_GLOBS:
        for p in sorted(root.glob(pattern)):
            if p.is_file():
                yield p


def check_dead_paths(root):
    findings = []
    for doc in iter_governance_files(root):
        rel_doc = doc.relative_to(root)
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for token in PATH_RE.findall(line):
                clean = token.rstrip("/.")
                if clean.startswith(ON_DEMAND_PREFIXES):
                    continue
                target = root / clean
                if not target.exists() and not list(root.glob(clean)):
                    findings.append("{}:{}  DEAD-PATH  {}".format(rel_doc, lineno, token))
    return findings


def check_skill_drift(root):
    """Return (findings, info). Findings fail the run; info is advisory.

    MISSING-SKILL (finding): a kebab-case token in a CLAUDE.md.example table row
    with no skills/<name>/ directory: the routing table points at nothing.
    UNLISTED-SKILL (info): a skill directory never mentioned in CLAUDE.md.example.
    Not a defect (skills auto-trigger from their own description; the table is a
    curated map), but useful input for the agent pass.
    """
    findings, info = [], []
    claude_md = root / "CLAUDE.md.example"
    skills_dir = root / "skills"
    if not claude_md.is_file() or not skills_dir.is_dir():
        return findings, info
    text = claude_md.read_text(encoding="utf-8")
    skill_dirs = {p.name for p in skills_dir.iterdir() if p.is_dir()}

    mentioned = set(BACKTICK_TOKEN_RE.findall(text))
    # Only kebab-case tokens inside table rows are treated as skill references:
    # single-word tokens (`make`, `commit`) are indistinguishable from commands.
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        for token in BACKTICK_TOKEN_RE.findall(line):
            if "-" in token and token not in skill_dirs:
                findings.append(
                    "CLAUDE.md.example:{}  MISSING-SKILL  {}".format(lineno, token)
                )
    for name in sorted(skill_dirs - mentioned):
        info.append("CLAUDE.md.example:-  UNLISTED-SKILL  {} (advisory)".format(name))
    return findings, info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repo root (default: cwd)")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    drift_findings, drift_info = check_skill_drift(root)
    findings = check_dead_paths(root) + drift_findings
    for f in findings:
        print(f)
    for i in drift_info:
        print(i)
    if findings:
        print("\n{} stale reference(s). Fix, or feed to the doc-gardening agent pass.".format(len(findings)))
        sys.exit(1)
    print("PASS  doc-gardening (no stale references)")
    sys.exit(0)


if __name__ == "__main__":
    main()
