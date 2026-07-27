# ABOUTME: Change contract for the declared complexity budget in plans (rounds, writers, sub-agents, minimum evidence)
# ABOUTME: Source: Graph Engineering note (July 2026) §VIII-B, "every run should declare its limits before adding workers"

# Harness Change Contract: plans declare a complexity budget

## Component

`rules/plan-first-workflow.md`: new `## Budget` section, and `budget` added to the step-2 draft checklist.

## Failure mode targeted

Run limits are implicit and scattered: the 5-round fix ceiling lives in the orchestrator protocol, the parallelism caps in a different table, and there is no stated ceiling at all for total sub-agents or for what counts as enough evidence to finalize. A run therefore cannot say what it spent against what it was allowed, and an exhausted run tends to end in a fluent summary that reads like success (the note's "do not hide partial failure behind a fluent final answer").

## Predicted improvement

Over the next 10 non-SKIP_SET plans: every plan file contains a `## Budget` block (target 10/10), and any run that stops on a limit names the limit in its final message rather than presenting partial work as complete. Sample needed to detect the second effect: at least 2 budget-exhausted runs.

## Invariants preserved

- The 5-round ceiling keeps its current value and its escalation behaviour; it is restated as a budget default, not changed.
- Parallelism caps (3 write agents, 5 when scopes are disjoint) keep their current values.
- Budget lives in exactly one place. If the orchestrator protocol later needs it, it points here rather than re-inlining the numbers.
- SKIP_SET tasks stay exempt: no budget block is required for a typo fix.

## Falsification

If, over the next 10 plans, the Budget block is present but every run's actual spend is invented after the fact to match it (no run ever reports hitting a limit, while sessions still escalate or stall), the block is ceremony: revert.

Second falsifier: if a plan's budget is used to justify stopping short of a deliverable that the task required ("budget said 3 sub-agents so I skipped the last workstream"), the budget is being read as permission to under-deliver: revert and move the limits back to the orchestrator as ceilings, not allowances.

## Rollback

`git revert <commit>`. Affects: `rules/plan-first-workflow.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 1 plan written since merge, of a 10-plan window | insufficient data on the falsifier, but the first half of the prediction is already missing: of the plans on disk only the two authored in this contract's own session carry a ## Budget block, and the single plan written since (2026-07-27_swarm-forge-borrowings.md) has none, giving 0 of 1 compliance; the cause is nameable and fixable, skills/plan-forge/references/plan-template.md is what actually generates plans and its 9 headings include no Budget section, so the rule and the generator disagree | kept |
