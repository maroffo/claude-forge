# ABOUTME: Change contract — backgrounded reviewers are joined at Finding Consolidation, counted on REVIEW-ARTIFACT
# ABOUTME: One failure mode: a launched-but-unreturned reviewer reads as a clean one

# Harness Change Contract: review join barrier

## Component

Rule `rules/orchestrator-protocol.md` (`agents=<returned>/<launched>` on `REVIEW-ARTIFACT`), skill `skills/orchestrator/SKILL.md` (Finding Consolidation steps 0 and 0b), hook `hooks/review-budget-guard.py` (join branch), tests.

## Failure mode targeted

With reviewers backgrounded, the loop can reach SCORE while a reviewer has not reported. Nothing distinguishes "reviewer found nothing" from "reviewer never returned", and the natural place to wait (FIX) is skippable: zero Critical/Major routes straight to SCORE, which is exactly the path where the omission is invisible. Raised as a must-fix by all three second-opinion reviewers (2026-07-28).

## Predicted improvement

Every review round records its launched roster and prints `agents=<returned>/<launched>`; a SCORE with an imbalance is blocked. Measurable: in traced sessions using background review, 100% of SCORE events are preceded by a balanced artifact line, and any truncated agent appears as a Major finding rather than silence.

## Invariants preserved

- The barrier is consolidation, not FIX: it holds on the zero-findings path too.
- Artifact lines without `agents=` (legacy) produce no join opinion.
- Only the LAST artifact line gates: an imbalance in round 1 resolved by round 2 does not block.
- Snapshot integrity: consolidation checks the tree still matches the reviewed SHA, so line-anchored findings are never applied to a moved tree.
- A truncated (capped) agent counts as returned only once its Major finding exists, so the count cannot be balanced by discarding a reviewer.

## Falsification

A session reports balanced `agents=` while a reviewer's findings are demonstrably absent from the round's findings file (the count is being asserted rather than derived), or the snapshot check fires so often it is routinely ignored (>30% of rounds).

## Rollback

Remove the join branch from the hook and the `agents=` field from the literal; consolidation reverts to prose ordering.

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
