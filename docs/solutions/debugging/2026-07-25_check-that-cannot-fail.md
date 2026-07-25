# ABOUTME: A deletion made a drift check structurally unable to fail; PASS and "not running" are indistinguishable
# ABOUTME: Detect by running the tool on both sides of the merge base, not by reading the diff

# Problem

A PR deleted the 40-row skill table from `CLAUDE.md.example` (correct: it was duplicated by the skill descriptions). `scripts/doc_gardening.py::check_skill_drift` only emitted its MISSING-SKILL finding for kebab-case tokens found *inside a table row of that file*. With no rows left, the finding became unreachable for every possible input: the check reported PASS unconditionally.

Nothing in the diff shows this. The diff shows an intended deletion of a table, in one file, and a checker that was not touched at all. The two facts only connect when you run the checker.

Worse, the advisory half inverted: UNLISTED-SKILL fires for any skill directory not mentioned in the scanned file, so it went from a handful of lines to roughly fifty, one per skill, burying the real output.

The consequence was measurable in the same PR: eleven Minor findings, nearly all dead cross-references, in a change that moved 1799 words between files. The sweep that exists to catch exactly that had been switched off by the same commit range.

# Solution

Run the tool on both sides of the merge base and compare, before trusting a green result on a branch that touched anything the tool reads:

```sh
uv run --no-project python3 scripts/doc_gardening.py --root . >/dev/null 2>&1; echo "BRANCH exit=$?"
git checkout -q origin/main
uv run --no-project python3 scripts/doc_gardening.py --root . >/dev/null 2>&1; echo "MAIN   exit=$?"
git checkout -q -
```

```
BRANCH exit=0     PASS  doc-gardening (no stale references)
MAIN   exit=1     4 stale reference(s). Fix, or feed to the doc-gardening agent pass.
```

Green on the branch and red on main is not automatically progress. Here nothing was fixed: the detector lost its input.

Then prove the repaired check is still reachable, which a passing run never demonstrates:

```sh
printf '| Bogus | `totally-not-a-skill` | injected |\n' >> skills/_INDEX.md
uv run --no-project python3 scripts/doc_gardening.py --root .   # must report MISSING-SKILL, exit 1
git checkout -- skills/_INDEX.md
```

The repair itself retargeted the check at `skills/_INDEX.md`, the catalog that survived, with two exemptions that stop it firing on facts instead of defects: names of `rules/*.md` files (the index cites rules beside skills) and gitignored skills that live in their own repo and are symlinked in locally. Gitignore entries may be globs (`skills/*-wishew`), so matching uses `fnmatch`, not equality. Verified against a simulated clean checkout, with the nine machine-local skills hidden, to confirm zero false positives for anyone who is not the author.

# Why It Works

A check has two states worth distinguishing, and exit 0 collapses them: "ran and found nothing" and "cannot find anything". Only an injected known-bad input separates them. Running both sides of the merge base catches the transition, and the injection catches the steady state, so the pair covers a check that was born dead as well as one that died in this commit.

The generalization: after deleting a structure, grep for what keys on it. A parser, a linter, a telemetry extractor or a test fixture that reads a format you just removed does not fail loudly, it goes quiet, and quiet reads as healthy.
