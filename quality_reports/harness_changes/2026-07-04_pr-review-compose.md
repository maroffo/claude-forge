# ABOUTME: Change contract for restructuring pr-review from duplicating to composing the review tiers
# ABOUTME: Failure mode = pr-review re-runs the orchestrator fleet and double-invokes second-opinion (6 Docker launches per PR)

# Harness Change Contract: pr-review composes, never re-implements

Authored before landing. From the 2026-07-04 skill/hook audit (workflow SEVERE: three overlapping heavyweight review paths with no selection rule).

## Component

Skill: `skills/pr-review/SKILL.md` (tier-selection preamble; fleet phase replaced by a reference to the orchestrator routing table; threshold table replaced by a reference to quality-gates; second-opinion reduced to one gated invocation; commit-narrative phase kept intact).

## Failure mode targeted

A single PR review could fire the specialized agent fleet twice (orchestrator already ran it in-loop), plus gemini-review, plus second-opinion twice unconditionally (6 Docker containers), with duplicated-and-already-drifted copies of the routing and threshold tables steering it. Cost disproportionate, and the copies disagree with the rules they were copied from.

## Predicted improvement

Per-PR review cost drops by roughly the duplicated fleet run plus 3 Docker launches, with zero table drift (references instead of copies). Checkable on the next 3 PR reviews: one fleet run total, at most one second-opinion, verdicts consistent with rules tables.

## Invariants preserved

- The commit-narrative reclassification phase (the skill's unique value) is unchanged.
- Severity vocabulary: Critical/Major/Minor per quality-gates.
- Trigger phrases unchanged ("pr review", "review PR", "review pull request").
- second-opinion still fires when reviewer verdicts genuinely conflict.

## Falsification

If in the next 5 PR reviews a defect ships that the removed duplicate fleet pass would have caught (i.e. the in-loop review demonstrably missed it and the duplicate would not have), the duplication was load-bearing: restore a targeted second pass for that finding class only.

## Rollback

`git revert <commit>`. Affects skills/pr-review/SKILL.md (+ any new references/ files).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 3 PR reviews (2026-07-25 round over PRs #100, #11, #1) | one reviewer fleet per PR (four domain reviewers, no duplicate pass), second-opinion gated to conflicts only, routing and threshold tables still references not copies, no shipped defect attributed to the removed duplicate pass | kept |
