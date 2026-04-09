# ABOUTME: Quality scoring thresholds — 80 commit, 90 PR, 95 excellence
# ABOUTME: Rubric-based scoring with auto-fail conditions for critical issues

# Quality Gates

## Thresholds

| Score | Gate | Action |
|-------|------|--------|
| < 80 | Commit blocked | Fix critical/major issues first |
| ≥ 80 | Commit OK | Safe to commit |
| ≥ 90 | PR ready | Safe to open PR |
| ≥ 95 | Excellence | Ship with confidence |

## Scoring Rubric

**Critical (auto-fail, score = 0):**
- Tests failing
- Build broken
- Security vulnerability (injection, leaked secrets)
- Data loss risk
- Unplanned stub implementation (TODO, pass, NotImplementedError not in plan)
- Destructive action disproportionate to task scope

**Major (-10 each):**
- Missing test coverage for new code
- Error handling gaps
- Performance regression
- Breaking API change without migration
- Blast radius contradiction (doc/test references old behavior after API change)
- Unjustified deletion of >20% of a file or removal of existing functions

**Minor (-3 each):**
- Style inconsistencies
- Missing documentation for public APIs
- Suboptimal but functional implementation
- TODO without tracking issue
- Stale comment or doc referencing removed/changed logic

## How to Score

After review agents report findings:
1. Count Critical → if any, score = 0, must fix
2. Start at 100, subtract Major (-10) and Minor (-3)
3. Compare against threshold for intended action (commit/PR)
4. If below threshold, fix and re-score
