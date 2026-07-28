#!/usr/bin/env python3
# ABOUTME: Guards the *-reviewer agent definitions: worktree-confinement line present, no tools: allowlist
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_agent_definitions.py

import glob
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
REVIEWER_GLOB = os.path.join(ROOT, "agents", "*-reviewer", "AGENT.md")

# The 7 reviewers routed by the orchestrator's review fleet. The glob is the
# source of truth (a NEW *-reviewer directory is picked up automatically and
# fails until it carries the confinement line); this floor only stops an empty
# or broken glob from passing vacuously.
MIN_REVIEWERS = 7

# Agents deliberately outside the isolation change (plan 2026-07-29, decision 3):
# write-capable or not run concurrently with the writer. The test asserts they
# are NOT enforced, i.e. nothing here is required to carry the line.
NON_REVIEWER_AGENTS = [
    "research-analyst",
    "software-engineer",
    "software-engineer-pi",
    "harness-mechanic",
    "project-analyzer",
    "tech-writer",
]

CONFINEMENT = "isolated git worktree copy of the repo at a named base SHA"

# Top-level YAML key: no leading whitespace, so `tools:` mentioned in prose or
# nested under another key does not false-positive.
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):", re.MULTILINE)


def reviewer_files():
    files = sorted(glob.glob(REVIEWER_GLOB))
    assert len(files) >= MIN_REVIEWERS, f"expected at least {MIN_REVIEWERS} *-reviewer definitions, found {len(files)}: {files}"
    return files


def split_frontmatter(path):
    """Return (frontmatter_block, body). AGENT.md must open with the --- block
    (check_repo.py's 'frontmatter first' check enforces that separately)."""
    text = open(path).read()
    assert text.startswith("---\n"), f"{rel(path)}: does not open with YAML frontmatter"
    end = text.find("\n---\n", 3)
    assert end != -1, f"{rel(path)}: frontmatter block is not closed"
    return text[4:end + 1], text[end + 5:]


def rel(path):
    return os.path.relpath(path, ROOT)


def test_frontmatter_has_name_and_description(files):
    for path in files:
        fm, _ = split_frontmatter(path)
        keys = TOP_LEVEL_KEY_RE.findall(fm)
        for required in ("name", "description"):
            assert required in keys, f"{rel(path)}: frontmatter is missing {required!r} (agent will not register)"


def test_no_tools_allowlist(files):
    """Pins the locked rejection (plan 2026-07-29, decision 2): a tools: allowlist
    is theatre with Bash and kills empirical review without it. Two independent
    reviewers rejected it on 2026-07-28; this fails if someone re-adds it."""
    for path in files:
        fm, _ = split_frontmatter(path)
        keys = TOP_LEVEL_KEY_RE.findall(fm)
        assert "tools" not in keys, (
            f"{rel(path)}: declares a 'tools:' key. Rejected 2026-07-28: with Bash an allowlist is theatre, "
            "without Bash it kills the mutation runs and executable probes reviews depend on. "
            "Isolation (isolation=\"worktree\") is the mechanism, not tool denial."
        )


def test_body_carries_confinement_line(files):
    for path in files:
        _, body = split_frontmatter(path)
        assert CONFINEMENT in body, (
            f"{rel(path)}: body does not state worktree confinement. Expected a sentence containing "
            f"{CONFINEMENT!r} (see agents/security-reviewer/AGENT.md '## Rules')."
        )


def test_non_reviewer_agents_are_not_enforced(files):
    """Scope guard: enforcement is exactly the *-reviewer glob. These agents exist
    and are intentionally untouched, so no assertion is made on their content."""
    enforced = {os.path.basename(os.path.dirname(p)) for p in files}
    for name in NON_REVIEWER_AGENTS:
        path = os.path.join(ROOT, "agents", name, "AGENT.md")
        assert os.path.exists(path), f"agents/{name}/AGENT.md is missing (update NON_REVIEWER_AGENTS if the agent was removed)"
        assert name not in enforced, f"agents/{name} is matched by the reviewer glob but listed as out of scope"


def main():
    files = reviewer_files()
    test_frontmatter_has_name_and_description(files)
    test_no_tools_allowlist(files)
    test_body_carries_confinement_line(files)
    test_non_reviewer_agents_are_not_enforced(files)
    print(f"test_agent_definitions: all tests passed ({len(files)} reviewer definitions)")


if __name__ == "__main__":
    main()
