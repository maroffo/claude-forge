#!/usr/bin/env python3
# ABOUTME: Guards the *-reviewer agent definitions: shared confinement block intact, no tools: allowlist
# ABOUTME: Run with: uv run --no-project python3 hooks/tests/test_agent_definitions.py

import glob
import hashlib
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
REVIEWER_GLOB = os.path.join(ROOT, "agents", "*-reviewer", "AGENT.md")

# The 7 reviewers routed by the orchestrator's review fleet. The glob is the
# source of truth (a NEW *-reviewer directory is picked up automatically and
# fails until it carries the block); this floor only stops an empty or broken
# glob from passing vacuously.
MIN_REVIEWERS = 7

# Agents deliberately outside the isolation change (plan 2026-07-29, decision 3):
# write-capable or not run concurrently with the writer.
NON_REVIEWER_AGENTS = [
    "research-analyst",
    "software-engineer",
    "software-engineer-pi",
    "harness-mechanic",
    "project-analyzer",
    "tech-writer",
]

# The shared block is byte-identical across the 7 files. These two lines bound it;
# the hash comparison is what catches drift in the bullets between them.
BLOCK_START = "- **Read-only with respect to the main tree.**"
BLOCK_END = "- No `tools:` allowlist is declared"

# Sentences that must survive verbatim, each the fix for a round-1 Major:
# confinement itself, the shared-.git boundary (M1), the fail-closed guard (M2).
PINNED = [
    "You run in an isolated git worktree copy of the repo at a named base SHA.",
    "never mutate shared git state",
    "`git rev-parse --git-dir` must differ from `git rev-parse --git-common-dir`",
]

# The confinement sentence is the one a reader could invert while keeping the
# words ("it is false that You run in an ..."). The other two pins carry their own
# negations by design ("never mutate ...", "must differ ..."), so scanning their
# context for negation words would fail by construction.
NEGATION_SCANNED = PINNED[0]
NEGATION_WINDOW = 60
NEGATION_RE = re.compile(r"\b(?:not|never|n't|false|without|neither|nor)\b", re.IGNORECASE)

# Top-level YAML key, strict form: used for name/description presence.
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):", re.MULTILINE)
# Rejection form, deliberately wider: quoted keys ("tools":) and space-before-colon
# (tools :) are valid YAML and were both green against the strict regex.
TOOLS_KEY_RE = re.compile(r"""^[ \t]*['"]?tools['"]?[ \t]*:""", re.MULTILINE)


def rel(path):
    return os.path.relpath(path, ROOT)


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


def confinement_block(path, body):
    """The shared bullet block, start line through end line inclusive."""
    lines = body.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(BLOCK_START)]
    ends = [i for i, line in enumerate(lines) if line.startswith(BLOCK_END)]
    assert len(starts) == 1, f"{rel(path)}: expected 1 line starting {BLOCK_START!r}, found {len(starts)}"
    assert len(ends) == 1, f"{rel(path)}: expected 1 line starting {BLOCK_END!r}, found {len(ends)}"
    assert starts[0] < ends[0], f"{rel(path)}: confinement block bounds are inverted"
    return "".join(lines[starts[0]:ends[0] + 1])


def test_frontmatter_has_name_and_description(files):
    for path in files:
        fm, _ = split_frontmatter(path)
        keys = TOP_LEVEL_KEY_RE.findall(fm)
        for required in ("name", "description"):
            assert required in keys, f"{rel(path)}: frontmatter is missing {required!r} (agent will not register)"


def test_no_tools_allowlist(files):
    """Pins the locked rejection (plan 2026-07-29, decision 2): a tools: allowlist
    is theatre with Bash and kills empirical review without it. Two independent
    reviewers rejected it on 2026-07-28; this fails if someone re-adds it, in
    quoted or spaced form."""
    for path in files:
        fm, _ = split_frontmatter(path)
        match = TOOLS_KEY_RE.search(fm)
        assert match is None, (
            f"{rel(path)}: frontmatter declares a 'tools:' key ({match.group(0).strip()!r}). "
            "Rejected 2026-07-28: with Bash an allowlist is theatre, without Bash it kills the mutation runs "
            "and executable probes reviews depend on. Isolation (isolation=\"worktree\") is the mechanism, not tool denial."
        )


def test_body_carries_pinned_sentences(files):
    for path in files:
        _, body = split_frontmatter(path)
        for sentence in PINNED:
            at = body.find(sentence)
            assert at != -1, (
                f"{rel(path)}: body is missing a pinned sentence of the confinement block: {sentence!r} "
                "(see agents/security-reviewer/AGENT.md '## Rules')."
            )
            if sentence is NEGATION_SCANNED:
                window = body[max(0, at - NEGATION_WINDOW):at]
                window = window[window.rfind("\n") + 1:]
                assert not NEGATION_RE.search(window), (
                    f"{rel(path)}: the confinement sentence is negated by its context: ...{window.strip()!r} "
                    f"{sentence!r}. The pin exists to assert the reviewer IS isolated."
                )


def test_block_is_identical_across_reviewers(files):
    """The block is a shared contract, not per-file prose: 7 copies, one hash.
    Without this, bullets between the pinned sentences drift file by file."""
    digests = {}
    for path in files:
        _, body = split_frontmatter(path)
        digest = hashlib.sha256(confinement_block(path, body).encode()).hexdigest()
        digests.setdefault(digest, []).append(rel(path))
    assert len(digests) == 1, (
        "confinement block is not byte-identical across reviewers; groups: "
        + " | ".join(f"{d[:12]}: {', '.join(paths)}" for d, paths in sorted(digests.items()))
    )


def test_non_reviewer_agents_stay_out_of_scope(files):
    """Scope pin (decision 3): isolation applies to *-reviewer agents only. If one
    of these is deliberately brought in scope later, drop it from this list in the
    same change, so the widening is visible in the diff."""
    for name in NON_REVIEWER_AGENTS:
        path = os.path.join(ROOT, "agents", name, "AGENT.md")
        assert os.path.exists(path), f"agents/{name}/AGENT.md is missing (update NON_REVIEWER_AGENTS if the agent was removed)"
        _, body = split_frontmatter(path)
        assert PINNED[0] not in body, (
            f"agents/{name}/AGENT.md carries the reviewer confinement sentence but is listed as out of scope "
            "(decision 3). Either the agent is now worktree-isolated, in which case drop it from NON_REVIEWER_AGENTS, "
            "or the line was copied there by mistake."
        )


def main():
    files = reviewer_files()
    test_frontmatter_has_name_and_description(files)
    test_no_tools_allowlist(files)
    test_body_carries_pinned_sentences(files)
    test_block_is_identical_across_reviewers(files)
    test_non_reviewer_agents_stay_out_of_scope(files)
    print(f"test_agent_definitions: all tests passed ({len(files)} reviewer definitions)")


if __name__ == "__main__":
    main()
