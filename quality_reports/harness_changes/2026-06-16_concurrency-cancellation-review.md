# ABOUTME: Change contract for the concurrency-cancellation review sections in the golang and python skills
# ABOUTME: Failure mode = async/cancellation assumed but silently dropped (learning Pattern 5)

# Harness Change Contract: concurrency-cancellation review sections

Authored before landing. Linked from the commit body. Append-only after merge. Implements Pattern 5 from `quality_reports/learning_corpus/recurrence-report.md`.

## Component

Skill content: `skills/golang/SKILL.md` (Concurrency section) and `skills/python/SKILL.md` (Code Review Checklist). Advisory review guidance only; no executable behavior.

## Failure mode targeted

Code assumes `async`/goroutine/`range channel` gives safe concurrency or honors cancellation, but it blocks the loop, races a shared buffer, or hangs forever on a context that never fires. Recurred across 2 products plus 2 side-projects (8 corpus members): Go `for range channel` cancellation traps and `nil` context (golem), shared `AsyncSession` and CPU-on-event-loop (feed-brain), shared-buffer data race and WebSocket shutdown deadlock (mirsad, wasit). The defining property: it works in tests with prompt-closing mocks, then hangs or panics in prod.

## Predicted improvement

A reviewer (or the human) reading the golang/python skill now has named anti-patterns to grep for on any concurrency-touching change, surfacing at least one of these before the "works in tests, hangs in prod" gap. Target: the next time a `range chan` over an external stream or a shared async session is introduced, it is caught at review rather than in production.

## Invariants preserved

- Skills stay advisory: this changes what reviewers look for, not how code is written or executed.
- Existing skill content is untouched (additions only, no rewrites or deletions).
- The Go guidance explicitly exempts idiomatic, provably-safe `range chan` (channel you own and is guaranteed to close), so correct code is not flagged.
- `make check` / `make test-e2e` stay green (no em-dashes on the skills surface, ABOUTME and frontmatter intact).

## Falsification

If reviewers begin flagging idiomatic, provably-safe `range chan` (channels with a guaranteed close) as defects, the guidance is causing churn on correct code: tighten the exemption wording or revert. If across many concurrency PRs the section never surfaces a real issue, it is dead weight: revert.

## Rollback

`git revert <commit>`. Affects: `skills/golang/SKILL.md`, `skills/python/SKILL.md`. Remove only the added "Cancellation traps" block and the two async checklist items.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions, all in a Python and shell harness repo | insufficient data: the guidance applies to Go channel or async-Python concurrency changes and no such change was reviewed in the corpus, so neither the "catches a cancellation trap" prediction nor the "flags idiomatic range chan" falsification could occur. Re-check after the next golem or mirsad concurrency work | kept |
