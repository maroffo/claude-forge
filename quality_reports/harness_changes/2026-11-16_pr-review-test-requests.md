# ABOUTME: Change contract: pr-review Test requests rule (no mutation hunting, no killing-test blocks, tests only for costly regressions)
# ABOUTME: Targets review-supplied tests pasted verbatim into the codebase as low-value test bloat

# Harness Change Contract: pr-review stops manufacturing tests

## Component

`skills/pr-review/SKILL.md` (Finding Rules, Test requests; Phase 3 test-reviewer brief line; Phase 5 scoring note), `skills/pr-review/references/evidence.md` (Deliverable: red-green tests are the only test code), `skills/pr-review/references/output-format.md` (no code in Minors). Scope is PR review only: `rules/quality-gates.md` and `agents/test-reviewer/AGENT.md` are unchanged (decision 2026-11-16, Max).

## Failure mode targeted

Reviews treat "no test pins this clause" and surviving mutants as findings and ship killing-test blocks; authors paste them verbatim (#8293's block landed byte-identical in #8299), filling the codebase with tests for guard clauses, nil checks, early returns and wiring. 38/50 of the last 50 pr-watch digests mention killing tests, mutants or unpinned code; the #8372 review alone carried K1-K3 for six integrity clauses, a nil guard and a `ctx.Err()` return. Max: "abbiamo riempito la codebase di test inutili" (2026-11-16).

## Predicted improvement

Over the next 20 pr-watch reviews: zero killing-test or mutant-table blocks; test-gap findings at most 1 per review and never Major except an unpinned bug fix; digests mentioning killing/mutant/unpinned fall from 38/50 to at most 3/20; test code in comments only inside demonstrated Critical/Major red-green blocks.

## Invariants preserved

- Phase 4b red-green evidence for bug claims stays mandatory.
- A PR that fixes a bug without a test that fails without the fix is still a Major.
- The implementing loop's own testing rules (verification-protocol, quality-gates) are untouched.

## Falsification

Revert or modify if, within 30 days, a regression lands on a path where a dropped test request would have caught it and that path is in the costly class (money, user data, auth, erasure, outage), or if reviews start reporting real bugs as "test gaps" to dodge the evidence gate.

## Rollback

`git revert <commit>`. Affects: skills/pr-review/SKILL.md, skills/pr-review/references/evidence.md, skills/pr-review/references/output-format.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
