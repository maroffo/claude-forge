# ABOUTME: Change contract for backporting failed-verify filtering to verify-before-stop
# ABOUTME: A failed test/lint/build command must not satisfy the verification gate

# Harness Change Contract: verify-before-stop — failed verify commands are not evidence

## Component

- Hook: `hooks/verify-before-stop.py` (evidence semantics in `scan()`/`main()`)
- Tests: `hooks/tests/test_verify_before_stop.py` (fixtures gain tool_use ids; new cases)

## Failure mode targeted

`verify-before-stop` counts a verification command as satisfying the gate by its *issuance*
alone: edit -> `make check` FAILS -> stop is allowed, because the hook never consults the
command's `tool_result`. The freshest computational signal is red, yet the gate reads
"verification ran". Surfaced by the architecture review of `score-evidence-guard`
(2026-07-05, sibling-inconsistency finding): two Stop hooks with visibly different
definitions of "verification ran" will confuse maintenance and telemetry.

## Predicted improvement

Evidence definition becomes identical across the two Stop hooks: a verify counts only if it
is correlatable (has a tool_use id), its result is not `is_error`, and it postdates both the
last source edit and the last failed verify (missing result keeps the benefit of the doubt).
Over the next 10 traced sessions: zero turns end with edits whose freshest check is red;
block frequency rises by less than 1 per session.

## Invariants preserved

- Fail-open on parse/IO errors; one nudge per turn via `stop_hook_active`.
- Docs-only and exempt-path turns are never blocked (existing cases 4, 7, 8, 11 unchanged).
- A successful check after the last edit still allows, exactly as today (case 2, 12).
- No shared-constant changes: the PR #59 drift guard (`test_hook_constants_sync.py`) is
  unaffected.

## Falsification

If over the next 10 traced sessions the hook blocks a turn whose verification actually
succeeded (false positive from result correlation, e.g. real transcripts emitting
tool_results without `tool_use_id`) more than once per session, the correlation assumption
is wrong: revert.

## Rollback

`git revert <commit>`. Affects: hooks/verify-before-stop.py,
hooks/tests/test_verify_before_stop.py.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions (13 with more than 3 events), 2026-06-08 to 2026-07-27 | insufficient data: hook blocks are recorded nowhere (traces carry only step events, zero PERMISSION_EVENT across the corpus), so neither the false-positive rate nor zero-turns-ending-red is observable; failed verifies do occur (40 VERIFY events with all three axes false) but cannot be tied to turn ends; re-check needs a hook-fire log | kept |
