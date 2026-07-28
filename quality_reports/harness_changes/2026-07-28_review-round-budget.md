# ABOUTME: Change contract — the fix-round budget becomes a countable literal enforced by a Stop hook
# ABOUTME: One failure mode: sessions score past the round ceiling instead of escalating

# Harness Change Contract: countable review-round budget

## Component

Rule `rules/orchestrator-protocol.md` (new `REVIEW-ROUND:` literal + step-6 note), hook `hooks/review-budget-guard.py` (round-count branch) with wrapper + registration, tests `hooks/tests/test_review_budget_guard.py`.

## Failure mode targeted

The fix-round budget (default 5, then escalate) is prose in plan-first-workflow and the protocol spine; nothing counts rounds. Measured: the worst sessions ran 8, 13 and 15 review rounds and still reported a SCORE instead of escalating (2026-07-28 measurement over 78 sessions). The 62.7 blocking minutes of the worst session are mostly rounds 6-8, i.e. work the budget said should not have happened.

## Predicted improvement

Sessions that print `REVIEW-ROUND:` cannot end a turn with a SCORE past the declared budget without an escalation line. Measurable in traces: the share of sessions exceeding their budget drops from 4/65 observed (6%, and 3 of the 4 worst-cost sessions) toward 0; any that remain carry an explicit escalation.

## Invariants preserved

- Legacy transcripts (no `REVIEW-ROUND:` and no `agents=`) behave exactly as before: the hook has no opinion.
- Fail-open on any exception, `stop_hook_active` short-circuit, one nudge per turn (score-evidence-guard discipline).
- The ceiling is inclusive: a SCORE at exactly `n == budget` passes.
- Raising the budget stays legitimate: an escalation line after the offending round satisfies the gate, so a deliberate, stated budget raise is not blocked.
- The hook never counts rounds itself: it reads what the loop declared. A loop that lies about its round number is a different failure, caught by the trace.

## Falsification

Sessions start under-reporting `n=` to stay under budget (round numbers stop matching the count of REVIEW-ARTIFACT lines in the same trace), or the block fires on sessions that legitimately raised the budget in their plan (false positives reported by Max more than twice in 20 sessions).

## Rollback

Remove the round-count branch from `review-budget-guard.py` (or unregister the hook); the `REVIEW-ROUND:` literal can stay as telemetry.

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
