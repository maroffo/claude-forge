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
- Overengineering: speculative abstraction for single-use code, unrequested configurability, error handling for unreachable scenarios (test: would a senior engineer call this overcomplicated? plan-mandated structure is exempt)

**Minor (-3 each):**
- Style inconsistencies
- Missing documentation for public APIs
- Suboptimal but functional implementation
- TODO without tracking issue
- Stale comment or doc referencing removed/changed logic
- Orphaned symbol: import/variable/function made unused by this same change and not removed

## Severity Vocabulary (canonical)

Every review path scores in **Critical / Major / Minor**. Tools that emit other vocabularies map here once; skills reference this table and never re-inline it (copies drift):

| Source | Their term | Maps to |
|--------|-----------|---------|
| advanced-review | CRITICAL | Critical |
| advanced-review | WARNING | Major |
| advanced-review | INFO | Minor |
| advanced-review | DISPUTED (unresolved after cross-check) | Major |

## Finding Contract

Every review path emits findings in the same five fields: **severity** (table above), **location** (`file:line`), **claim** (what is wrong), **fix** (what to do), **evidence** (the observation that would settle it: a red-green test, a command plus expected output, a CWE id, a grep-able convention reference, a complexity derivation).

Evidence is what makes a finding checkable instead of arguable: the fix loop verifies it, and the two-confirmation gate at SCORE has something to key on. A finding whose evidence you cannot name is not a finding, so drop it. Keeping it in the report by softening it to Minor is the exact failure mode this contract prevents.

## How to Score

Scoring runs over the **consolidated** finding list, never the raw agent reports: one defect counts once, however many agents reported it (consolidation procedure in the `orchestrator` skill, Finding Consolidation).

After review agents report findings and the reports are consolidated:
1. Count Critical → if any, score = 0, must fix
2. Start at 100, subtract Major (-10) and Minor (-3), once per consolidated finding
3. Compare against threshold for intended action (commit/PR)
4. If below threshold, fix and re-score
