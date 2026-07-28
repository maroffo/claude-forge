# ABOUTME: Change contract — bug-hunter-filed issues fast-path through triage on repro strength
# ABOUTME: One failure mode: hunter issues re-enter the loop without repro validation

# Harness Change Contract: agent:hunted fast-path

## Component

Skills `bug-hunter-hikma` (new) and `issue-triage-hikma` (scan filter + fast-path section), both in the claude-hikma-skills repo; new label `agent:hunted` on hikma-wasit. This contract lives in forge because it alters the autonomy gating of the issue loop.

## Failure mode targeted

Hunter-filed issues either (a) never reach the loop (the triage scan drops all `agent:*`-labeled issues, so `agent:hunted` was invisible by construction), or (b) reach it unvalidated: an issue claiming a repro that does not actually fail on HEAD would drive issue-loop into fixing a non-bug. The fast-path must make hunted issues claimable WITHOUT weakening the rubric.

## Predicted improvement

Hunted issues with a well-formed repro block + spec citation verdict `agent:ready` at the next triage pass with zero human touches (target: 100% of well-formed ones); malformed ones verdict `agent:needs-spec` and are counted in the triage report. Safe?/Scoped? remain independently verified by triage, never taken from the hunter's self-assessment.

## Invariants preserved

- Triage rubric runs in full on hunted issues; 🔴 classes still verdict `agent:human` regardless of repro quality.
- Human veto labels unchanged and final.
- The hunter never labels `agent:ready` itself: filing and readiness stay two separate judgments (hunter -> triage), unlike plan follow-ups where the orchestrator IS the triage-time judge.
- issue-loop's REPRODUCE step (W0) still runs the repro on HEAD before implementing: a hunted repro that passes on HEAD aborts the fix as not-a-bug.

## Falsification

A hunted `agent:ready` issue whose repro passes on HEAD at issue-loop's W0 (fabricated or stale bug), more than once in 10 hunted issues; or triage reports >30% malformed hunted issues (hunter template not doing its job); or a 🔴-class hunted issue reaches `agent:ready`.

## Rollback

Remove the fast-path section and the `agent:hunted` scan exception from issue-triage-hikma; hunted issues fall back to invisible-to-triage (and the hunter skill should then be paused).

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
