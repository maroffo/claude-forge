# ABOUTME: Change contract for adding active_min metric to harness-trace SUMMARY
# ABOUTME: Distinguishes session calendar span from actual model work time

# Harness Change Contract: add `active_min` to SUMMARY.metrics.trajectory_efficiency

## Component

`skills/harness-trace/src/harness_trace/extractor.py::_compute_summary` (and follow-up: `SKILL.md` docstring + new test in `test_extractor.py`). Schema models in `models.py` already accept arbitrary keys inside the `trajectory_efficiency` dict, so no schema bump.

## Failure mode targeted

The first real `harness-mechanic` analysis surfaced a SUMMARY where `duration_min = 4025` (67h) for a session that the user kept open across 3 calendar days. The number is technically correct as a calendar span (last_ts - first_ts) but is useless for any decision the Evolution Agent might want to make: "did this task cost 30 minutes or 67 hours of model work?" cannot be answered from the current field. Future cross-session aggregations (cost per task, throughput trends) would inherit the same contamination.

## Predicted improvement

Add `active_min` inside `metrics.trajectory_efficiency` = sum of inter-message gaps clamped to 300s (5 min). Each gap > 5 min is counted as exactly 5 min of "active work tail" and any further idle is dropped.

- For the current in-progress session (single sitting): `active_min` ≈ `duration_min` (both ~40 min). Delta near zero.
- For the April 67h session: `active_min` should land in the 60-300 min range (a few sittings over 3 days).
- After 5+ future sessions, cross-session aggregation against `active_min` becomes meaningful.

## Invariants preserved

- `duration_min` field unchanged and unchanged in semantics (calendar span). No consumer that already reads `duration_min` breaks.
- All 63 existing tests stay green.
- No schema version bump: `HarnessMetrics.trajectory_efficiency` is already `dict[str, Any] | None`, the new key is additive.
- v1 traces still parse (the metric only appears in newly generated traces).

## Falsification

- If on a real single-sitting session > 1 hour `active_min` returns less than `duration_min - 10`, the 300s ceiling is too aggressive and missing legitimate work tails. Raise ceiling to 600s or revert.
- If `active_min` ever exceeds `duration_min`, the math is wrong (active can never exceed span). Add an assertion.
- If for a 67h session `active_min` is still > 600 min (10h), the gap clamping is not working as designed.

## Rollback

```bash
git revert <commit>
```

Affects: `skills/harness-trace/src/harness_trace/extractor.py`, `skills/harness-trace/tests/test_extractor.py`, `skills/harness-trace/SKILL.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

Verdict: pending.
