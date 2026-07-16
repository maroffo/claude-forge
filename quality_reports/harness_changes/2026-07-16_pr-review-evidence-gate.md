# ABOUTME: Change-contract for the pr-review evidence gate (red-green tests for Critical/Major findings)
# ABOUTME: Findings must be demonstrated in the isolated clone, not just claimed; unproven claims escalate to second-opinion

# Harness Change Contract: pr-review Critical/Major findings require executable evidence

## Component

skill (`skills/pr-review/`): SKILL.md (new Phase 4b, gating changes to Phases 5-7), new `references/evidence.md`, updated `references/output-format.md`.

## Failure mode targeted

Delegated reviewers (agents and Gemini segments) report Critical/Major findings as prose claims. Plausible-but-wrong findings (hallucinated APIs, misread control flow) survive source-verification because "read the file:line" only checks the code exists, not that the defect is real. Max receives a report where a demonstrated bug and an unverified claim look identical, and false positives can block a merge.

## Predicted improvement

Every Critical/Major bug claim in the final report carries either a red-green test that failed in `$PR_REVIEW_DIR` or a non-executable evidence type from the taxonomy. Over the next 10 pr-review runs, at least one finding per ~3 runs is expected to be caught as unproven before the report (based on the "Hallucinations caught" rate observed so far); reports show 0 Critical/Major entries with no Evidence field.

## Invariants preserved

- pr-review keeps composing tiers: no re-implementation of advanced-review's sandboxed runner, no Docker dependency added.
- All test writes and runs happen inside `$PR_REVIEW_DIR`; the active repo stays read-only.
- Phase 8 cleanup semantics unchanged: the throwaway clone (including evidence tests) is always removed; surviving repro tests are copied into the report before deletion.
- Minor findings and the commit-narrative reclassification (Phase 4) are untouched.
- second-opinion stays gated: it fires for unproven Critical/Major and contested findings only, never unconditionally.

## Falsification

Any of, over the next 10 runs: (a) a finding discarded or downgraded as unproven is later confirmed real by the PR author or a production incident; (b) median pr-review wall-time more than doubles on a moderate PR (300-1000 lines); (c) an evidence test file leaks outside `$PR_REVIEW_DIR` into the active repo. Any one occurrence of (a) or (c) → revert.

## Rollback

`git revert <this commit>`. Affects: skills/pr-review/SKILL.md, skills/pr-review/references/evidence.md, skills/pr-review/references/output-format.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
