# ABOUTME: Change contract for the canonical severity vocabulary in quality-gates
# ABOUTME: Failure mode = advanced-review severities don't map to the scoring rubric, so /score can't consume its findings

# Harness Change Contract: canonical severity vocabulary

Authored before landing. From the 2026-07-04 skill/hook audit (workflow MODERATE): `/score` instructs deducting 10 per Major and 3 per Minor from review findings, but advanced-review emits CRITICAL/WARNING/INFO plus confidence tags, so the instruction cannot execute.

## Component

Rule: `rules/quality-gates.md` (new "Severity Vocabulary (canonical)" section with the advanced-review mapping table). Consumers (pr-review) reference it instead of re-inlining thresholds.

## Failure mode targeted

Two severity vocabularies with no defined mapping breaks the review-to-score pipeline: a WARNING from advanced-review has no defined point value, so scoring after a deep review is improvised per session, differently each time.

## Predicted improvement

Any session scoring after an advanced-review run applies the same deduction (WARNING=Major=-10, INFO=Minor=-3, unresolved DISPUTED=Major). Checkable on the next 5 scored reviews: zero improvised mappings.

## Invariants preserved

- Thresholds (80/90/95) and the existing Critical/Major/Minor rubric unchanged.
- Always-loaded rules grow by ~12 lines (one table).
- advanced-review itself (separate repo) is unchanged; the mapping lives rules-side so it applies regardless of that repo's version.

## Falsification

If advanced-review's vocabulary changes and the table silently mismatches (doc-gardening should catch the drift), or if DISPUTED=Major produces routinely inflated deductions on findings later shown false, adjust the row or revert.

## Rollback

`git revert <commit>` or delete the section in rules/quality-gates.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
