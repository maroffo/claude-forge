# ABOUTME: Change contract for the silent-success / fail-open review-checklist item in reviewer agents
# ABOUTME: Failure mode = a path returns success when the action was skipped (learning Pattern 1)

# Harness Change Contract: silent-success review-checklist item

Authored before landing. Linked from the commit body. Append-only after merge. Implements Pattern 1 (highest-value) from `quality_reports/learning_corpus/recurrence-report.md`.

## Component

Agent prompts: `agents/architecture-reviewer/AGENT.md` and `agents/security-reviewer/AGENT.md`, Scope sections. Adds a mandatory review question; no frontmatter/description change (auto-trigger surface unchanged).

## Failure mode targeted

Code or config returns a green/200/allow/no-error signal while the intended work silently did not happen, so tests and CI pass and the bug surfaces only in production. Broadest pattern in the corpus: 13 members across all 3 products (Casbin RBAC silently disabled by passthrough middleware, nil-service short-circuit to a "graceful" 200, OTel swallowing every export error, config drift returning `allow`, 372 green tests on a never-wired CLI, `pgtype.UUID.Scan` accepting garbage). The root: the absence of an action is indistinguishable from its success.

## Predicted improvement

Reviewers ask, for every success/allow/nil-error branch, whether a test fails if the action is skipped. Target: catch at least 1 silent-success defect per 5 feature PRs at review time instead of in prod (baseline: ~13 such bugs in the corpus, most found in prod or late). Note: the report's secondary "silent-success-advisor" grep hook is deliberately NOT implemented here, its own falsification row flagged a high noise risk; the checklist (human judgment) is the reliable half.

## Invariants preserved

- Reviewer agents stay read-only; output format unchanged.
- Addition only (one Scope bullet each), no edits to existing scope items.
- No change to the agents' `description` frontmatter, so routing/auto-trigger is unaffected.
- Legitimate, tested graceful-degradation paths are not to be flagged (the question is "is there a test that fails if the action is skipped", not "never degrade").

## Falsification

If over ~15 sessions reviewers rubber-stamp the new question without analysis (it appears in output but never surfaces a real finding), it is theater: remove it. If it generates repeated false BLOCK recommendations on correctly-tested degradation paths, the wording is too aggressive: soften or revert.

## Rollback

`git revert <commit>`. Affects: `agents/architecture-reviewer/AGENT.md`, `agents/security-reviewer/AGENT.md`. Remove the added Scope bullet from each.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
