# ABOUTME: Change contract — follow-up issues are filed triage-labeled (agent:ready when they pass the rubric)
# ABOUTME: One failure mode: follow-ups die unlabeled in the backlog, invisible to the autonomous loop

# Harness Change Contract: follow-ups born agent:ready

## Component

Skill reference `skills/plan-forge/references/plan-template.md` (W(last) follow-up drafting shape + DoD row 7) and the PR step of `issue-loop-hikma/SKILL.md` (claude-hikma-skills repo), which files them.

## Failure mode targeted

Follow-up issues drafted in plans are filed at PR time with no triage label, so issue-loop-hikma (which selects only `agent:ready`) never picks them up: autonomous work generates backlog that only manual triage can re-enter into the loop (requirement stated by Max, 2026-07-28).

## Predicted improvement

Follow-ups filed by the loop carry `agent:ready` (rubric passed at file time: drafted with what/where/done-when/verification) or `agent:needs-spec` (rubric not passed), never bare. Measurable: fraction of loop-filed follow-ups that a subsequent issue-loop run can claim without manual triage goes from 0 to the ready share; target >= 70% given the template forces the rubric fields at drafting time.

## Invariants preserved

- The triage rubric is not bypassed: `agent:ready` at filing requires the same four tests issue-triage-hikma applies; hard 🔴 exclusions (auth, destructive migrations, security surfaces) file as `agent:human`, exactly as triage would label them.
- Issue creation stays with the orchestrator at PR time (never subagents), unchanged from the template's existing rule.
- Existing manually-filed issues are untouched; triage keeps re-labeling authority (a bad ready label is correctable by the normal triage pass).

## Falsification

Loop-filed `agent:ready` follow-ups repeatedly bounce at implementation time for under-specification (issue-loop escalates or re-labels needs-spec on >30% of them), showing the file-time rubric is rubber-stamping; or a 🔴-class follow-up gets filed `agent:ready`.

## Rollback

Revert the two edits; follow-ups go back to being filed unlabeled.

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
