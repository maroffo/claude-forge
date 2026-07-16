# ABOUTME: Change-contract for domain slices in pr-review Phase 3 (token budget per reviewer)
# ABOUTME: Reviewers get the diff hunks of their routing domain plus declared exclusions, not the full diff

# Harness Change Contract: pr-review reviewers receive domain slices, not the full diff

## Component

skill (`skills/pr-review/SKILL.md`), Phase 3: delegated reviewers receive a token-budgeted slice of the diff scoped to their routing domain, with declared exclusions per the orchestrator page-fault rule. Idea imported from context-kernel T2 (task-relative slice under a token budget).

## Failure mode targeted

Every delegated reviewer receives the full diff regardless of domain: on large PRs (>1000 lines) the security reviewer reads docs hunks, the dx reviewer reads SQL, and each burns context on out-of-domain material. Dilution costs tokens and attention: in-domain findings compete with noise the reviewer was never routed for.

## Predicted improvement

Measured over the next 5 pr-review runs on PRs above 1000 lines: reviewer input shrinks from full diff to domain slice (expected 40%+ smaller briefs on multi-domain PRs); token per run drops correspondingly; in-domain findings per reviewer stay stable or rise. Small PRs are exempt, so no regression there.

## Invariants preserved

- The routing table stays in `rules/orchestrator-protocol.md`; pr-review keeps applying it without duplicating it.
- The full diff stays on disk (`/tmp/pr<N>-diff.patch`) and `$PR_REVIEW_DIR` stays available to every reviewer: any cut is a declared, recoverable page fault, never a hard wall.
- Simple PRs (< 300 lines) pass whole: slicing overhead only where dilution actually costs.
- Gemini segmentation (< 3000 lines per segment) is unchanged.

## Falsification

A reviewer misses a cross-domain defect that the full diff would have surfaced (for example a security flaw visible only in a hunk routed to another domain), traced to the slice in a post-mortem. One occurrence → widen the slice rule or revert.

## Rollback

`git revert <this commit>`. Affects: skills/pr-review/SKILL.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
