# ABOUTME: Change contract for the hot-path performance regression gate (baseline/compare in the orchestrator loop)
# ABOUTME: Hot-path tasks capture a bench baseline at LOCALIZE and compare at VERIFY; regression = review finding, never auto-fail

# Harness Change Contract: perf-regression-gate — hot-path tasks carry a baseline/compare delta

## Component

- Rule: `rules/orchestrator-protocol.md`, LOCALIZE (step 1a) — new BENCH-BASELINE sub-protocol row (hot-path trigger → `make bench-baseline` at task start).
- Rule: `rules/orchestrator-protocol.md`, VERIFY (step 2) — `make bench-compare` when a baseline exists; exit ≠ 0 ⇒ Major finding, not a fail.
- Rule: `rules/verification-protocol.md`, "After Every Code Change" — one pointer line for hot-path tasks.

Points at the mirsad side shipped in the same effort (`make bench-baseline` / `make bench-compare`,
`BENCH_REGRESSION_PCT` default 10, benchstat-significant-only gate, `tools/benchgate`; see the
hikma-mirsad ExecPlan `2026-07-12_perf-regression-gate.md`).

## Failure mode targeted

Hot-path performance regressions land silently. The gateway's redact/LSH/control path has
absolute-budget smoke tests but no relative before/after check in the loop: an accidental O(n²),
a per-request re-parse, or a 30% slowdown on a common size passes REVIEW because nothing measures
the delta against the pre-change code. Regressions get discovered in production, or never.

## Predicted improvement

Every hot-path task (touching mirsad `internal/{lsh,pii,decode,control,adapter,proxy,cache}`)
carries a baseline→compare delta into REVIEW, so a regression becomes an explicit accept-or-fix
decision recorded in the plan's Decisions table instead of an unnoticed slowdown. Qualitative;
evaluate over the next ~10 hot-path mirsad sessions (baseline: 0 sessions carry a delta today).

## Invariants preserved

- Non-hot-path tasks gain zero overhead: the trigger is path-scoped, so a task that touches no
  hot-path package never runs a benchmark.
- The gate never auto-blocks: `bench-compare` exit ≠ 0 is a **Major** review finding, resolved by
  fix or explicit accept-with-rationale — it is never an auto-fail and never a silent accept.
- LOCALIZE and VERIFY semantics are unchanged for every non-hot-path task; the existing file-list
  and test/lint/build checks are untouched.

## Falsification

Revert if, over the next 10 hot-path sessions, ANY of:
- the gate false-positive-fires more than 3 times (flags a delta with no real regression), or
- agents routinely skip the BENCH-BASELINE step (baseline missing at VERIFY on hot-path tasks), or
- the ~6 min baseline capture gets cited as a reason to skip the protocol / the task.

## Rollback

`git revert <commit>` — reverts the two rule hunks in one commit. Affects:
`rules/orchestrator-protocol.md`, `rules/verification-protocol.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
