# ABOUTME: Change-contract aiming reviewer robustness at the orchestrated flow, not just .sh scripts
# ABOUTME: Six fields from arxiv 2605.18747 §5.2.3; supersedes 2026-06-17_reviewer-failure-robustness.md

# Harness Change Contract: structural degradation on the path that actually runs

Supersedes `2026-06-17_reviewer-failure-robustness.md`. Authored before the change lands. Linked from the commit body. Append-only after merge.

## Component

Skill `skills/second-opinion/SKILL.md` (Step 4 explicit per-reviewer Bash-tool timeout + failure-classification procedure; Step 5 required reviewer-status line; EXIT trap for the temp prompt; optional OAuth-preflight troubleshooting note) plus the three reviewer scripts `docker/isolated-{reviewer,gemini,deepseek}/isolated-*-review.sh` (catch exit 124 → readable message + preserved exit code; DeepSeek default timeout 300→600).

## Failure mode targeted

The prior contract hardened the wrong code path. A three-reviewer `/second-opinion` run of the prior change surfaced (verified) that Step 4 inlines `docker run` and never calls the `.sh` scripts, so the timeout guard added to those scripts never executes in the orchestrated flow. That flow's only wall-clock bound is the Bash-tool timeout, whose 120s default kills `deepseek-reasoner` mid-reasoning; and the degradation instruction was prose with no failure predicate and no status slot, so a model could synthesize a `401` body as if it were an opinion.

## Predicted improvement

Over the next ~10 `/second-opinion` runs: (a) zero premature DeepSeek kills attributable to the 120s default (Step 4 now mandates 600s for DeepSeek); (b) every run emits a `Reviewer status:` line accounting for all three reviewers, 10/10; (c) on any reviewer failure, the synthesis proceeds from survivors and the failed one is reported with a reason, never glossed as an opinion.

## Invariants preserved

- The optional timeout guard stays best-effort: no `timeout`/`gtimeout` → prefix expands empty, `docker run` unchanged (verified: happy-path PONG, exit 0).
- The exit-124 catch preserves the real exit code for all non-timeout failures (verified: simulated exit 7 passes through with no spurious message).
- No change to isolation, mounts, key handling, or the identical-prompt guarantee.
- Build step and interactive login `docker run` remain unguarded (long/interactive by design).

## Falsification

If a run still aborts entirely because one reviewer failed, or omits the `Reviewer status:` line, the structural degradation is not working, revert the SKILL.md changes. If the exit-124 catch ever prints the timeout message for a non-124 failure, or swallows a real exit code, revert the script changes.

## Rollback

`git revert <commit>`. Affects: skills/second-opinion/SKILL.md, docker/isolated-deepseek/isolated-deepseek-review.sh, docker/isolated-gemini/isolated-gemini-review.sh, docker/isolated-reviewer/isolated-review.sh.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
