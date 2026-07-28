# ABOUTME: Change contract — review agents launch backgrounded with a harness-side 15-minute cap
# ABOUTME: One failure mode: a pathological reviewer blocks the loop with no way to bound it

# Harness Change Contract: background review + per-agent cap

## Component

Skill `skills/orchestrator/SKILL.md` (new Review Scheduling section + Scheduling column in the Parallelism table). No hook: the cap is a procedure the orchestrator executes (`TaskStop` on a backgrounded task), because the `Agent` tool exposes no timeout parameter.

## Failure mode targeted

A single architecture-reviewer run took 58.0 minutes, i.e. 20% of all blocking time measured across 65 sessions, with no way to bound it: a synchronous `Agent` launch cannot be capped at all (verified: the tool has no timeout parameter). Separately, four of the six longest recorded runs ended in `[Request interrupted by user]` — during a silent block, interruption was the user's only control.

## Predicted improvement

Reviewers no longer block the loop (the orchestrator does contract/plan/commit work meanwhile), and no single reviewer can consume more than ~15 minutes. Measurable in the next 20 sessions: zero reviewer runs above 15 minutes, zero user interrupts of a review wait, and background adoption for review agents at ~100% (from 20%).

## Invariants preserved

- The cap is never stated in the reviewer's prompt: an agent that knows its deadline satisfices, returning shallow findings that are indistinguishable from diligence (second-opinion must-fix).
- A stopped agent is `truncated`, never clean: it files a Major finding and blocks `converged=yes`. Major, not Critical, so an infra timeout costs a fix round instead of zeroing the score.
- The orchestrator never edits files under review while reviewers run (that would move the tree beneath them).
- 15 min sits above the measured p90 (6.1) with margin, so it truncates the pathology, not normal work.
- W0 precondition, verified before shipping: 84/84 historical background reviewer launches had their findings collected (strict attribution), so backgrounding does not introduce a known drop path.

## Falsification

Reviewer findings-per-round drops measurably after the change (backgrounding or the cap is costing recall), or truncations exceed ~5% of runs (the cap is too tight), or a session reports a SCORE with a truncated agent counted as completed.

## Rollback

Revert the Review Scheduling section: reviewers go back to synchronous launches and the cap becomes unenforceable again (the join barrier and round budget are independent and can stay).

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
