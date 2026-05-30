# ABOUTME: Change contract for per-subagent effort assignment (Opus 4.8)
# ABOUTME: Failure mode = reviewers/analysts burning orchestrator-level reasoning on bounded tasks

# Harness Change Contract: per-subagent effort assignment for Opus 4.8

Authored before landing. Linked from the commit body. Append-only after merge.

## Component

`agents/*/AGENT.md` (11 files: effort frontmatter added) + `rules/orchestrator-protocol.md` (new "### Effort assignment" section documenting the policy).

## Failure mode targeted

Subagents inherit the session effort level. On Opus 4.8 the orchestrator runs at `xhigh`, so read-only reviewers and research agents (bounded, single-pass analysis) reason at `xhigh` too: wasted reasoning tokens and latency on work that does not need orchestrator-grade deliberation. There is no per-role effort calibration in the harness today.

## Predicted improvement

Reviewer/research subagent reasoning tokens per dispatch drop materially (qualitative: `medium` allocates less thinking than `xhigh` on 4.8) with no loss in finding quality. Smallest sample to judge: compare reviewer subagent token usage in traces across the next ~10 review-bearing sessions vs the pre-change baselines in `quality_reports/token_baselines/`. Expect lower per-review subagent tokens, stable score-at-first-review.

## Invariants preserved

- Review agents stay read-only. software-engineer stays read-write and inherits session effort (no `effort:` line; `inherit` is invalid for effort).
- Effort values agree across agent frontmatter, the orchestrator table, and README.
- All AGENT.md files still pass `make test-e2e` (name=dir, description length) and `make check` frontmatter validation.
- No change to routing, parallelism caps, or quality gates.

## Falsification

If review quality drops (same class of MAJOR/CRITICAL findings missed by `medium` reviewers that `xhigh` would have caught, observed via re-review or escaped bugs) in 2+ sessions, OR if first-review score regresses vs baseline over the next 10 sessions, raise the affected reviewer back toward `high`/inherit or revert.

## Rollback

`git revert <commit>`. Affects: the 11 `agents/*/AGENT.md` (remove the `effort:` line) and `rules/orchestrator-protocol.md` (remove the "### Effort assignment" section).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
