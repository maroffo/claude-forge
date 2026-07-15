# ABOUTME: Change contract for adding an overengineering deduction to the quality-gates scoring rubric
# ABOUTME: Imports Karpathy's "bloated abstractions" failure mode as a scoreable Major finding

# Harness Change Contract: overengineering findings get a Major deduction in the scoring rubric

## Component

`rules/quality-gates.md`, Scoring Rubric, Major list: one new bullet for overengineering (speculative abstraction, unrequested configurability, error handling for unreachable scenarios).

## Failure mode targeted

architecture-reviewer's dimension list already includes "over-engineering, premature abstraction" (`agents/architecture-reviewer/AGENT.md:21`), but the Scoring Rubric has no corresponding deduction line. A review that flags speculative abstraction maps to nothing, moves the score by zero, and the bloated code passes the commit gate. Anticipated failure, imported from Karpathy's observed LLM coding pitfalls ("implement a bloated construction over 1000 lines when 100 would do", via multica-ai/andrej-karpathy-skills); 0 scored overengineering findings across the 6 traced sessions to date, consistent with the mapping being undefined rather than the failure being absent.

## Predicted improvement

Qualitative: overengineering findings become scoreable. Over the next 15 scored sessions, every over-engineering finding emitted by a reviewer carries a Major (-10) deduction in the SCORE breakdown instead of being dropped. Smallest sample to detect: the first session where a reviewer flags speculative abstraction.

## Invariants preserved

- Thresholds unchanged (80 commit / 90 PR / 95 excellence).
- No new auto-fail (Critical) condition: overengineering is Major, never score = 0.
- Severity Vocabulary mapping table unchanged.
- The deduction targets only speculative complexity: abstractions or configurability the plan explicitly requires are NOT findings under this bullet.

## Falsification

If over the next 10 sessions the bullet penalizes plan-mandated structure at least twice (reviewer cites the bullet, engineer shows the plan required the abstraction), or fix rounds per session go UP because engineers strip structure that later has to be re-added, the bullet is miscalibrated: revert.

## Rollback

`git revert <commit>`. Affects: `rules/quality-gates.md` only.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
