# ABOUTME: Change contract for the learning-loop skill (cross-repo LEARNING.md mining to harness changes)
# ABOUTME: Failure mode = recurring failure-modes hide because retrospectives are per-repo and never aggregated

# Harness Change Contract: learning-loop skill

Authored before landing. Linked from the commit body. Append-only after merge.

## Component

Skill: `skills/learning-loop/` (new `SKILL.md`). Supporting non-harness code: `scripts/learning_corpus.py` (deterministic ingest), a `learning-corpus` target in `Makefile`, and a `.gitignore` entry for `quality_reports/learning_corpus/`.

## Failure mode targeted

The same failure shape recurs across repos and goes unaddressed because each `LEARNING.md` is read in isolation. Concrete evidence from the first run: the "silent success / fail-open / no-op" shape appears in 5 distinct repos across all 3 products (wasit, mirsad, weaponizer, Wishew, golem); "async is not concurrent / cancellation dropped" in 4; "build-time value baked in" in 3. None of these had triggered a process change, because no step ever looked across repos. A per-repo retrospective (`learning-docs`) cannot see recurrence; trace analysis (`harness-mechanic`) cannot see it either, because a green test that lies leaves no trace signal.

## Predicted improvement

A periodic run surfaces every failure shape spanning 2+ repos and proposes one mechanical harness action per shape with a falsifiable contract. Target: each run converts at least one cross-product pattern into a landed hook/rule/checklist change. Over successive runs, the repeat-pattern rate (share of last run's patterns that recur) should trend down for any pattern that got a mechanical fix. Verifiable now: `make learning-corpus` produces a 290-learning corpus from 22 files in under a second, and the agent pass produced 7 ranked patterns with contracts on the first run.

## Invariants preserved

- The ingest phase stays deterministic and offline (no LLM, no network): rerunnable for free, reproducible.
- The corpus and report are never committed (gitignored): they hold private incident detail from work repos.
- The skill never runs autonomously: it is a human-scheduled review, not a hook (no auto-trigger on session events).
- One failure mode per emitted change-contract: ambiguous falsification is disallowed.
- `make check` and `make test-e2e` stay green (SKILL.md schema: name=dir, description length, 2 ABOUTME lines, no em-dashes on the skills surface).
- Recurrence counting collapses same-repo path variants and groups products, so cross-repo claims are honest.

## Falsification

If two consecutive runs propose the same patterns and none get implemented, the loop is generating noise the human ignores: stop running it, or cut it to ingest-only. If a proposed harness action lands and its own falsification row later fires (the change made things worse), that is a miss of this loop's triage, not just the individual change: tighten the "prefer cheap mechanical wins" rule. If the agent pass routinely emits forced patterns (clusters that are 2 unrelated items sharing a keyword), the threshold or prompt is wrong: revert to ingest-only and triage by hand.

## Rollback

`git revert <commit>` then `rm -rf skills/learning-loop`. Affects: `skills/learning-loop/SKILL.md`, `scripts/learning_corpus.py`, `Makefile` (the `learning-corpus` target and `.PHONY`/help lines), `.gitignore` (the `quality_reports/learning_corpus/` entry). The gitignored corpus/report artifacts can be deleted with `rm -rf quality_reports/learning_corpus`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
