# ABOUTME: Change contract: VERIFY entries resolve pass/fail from paired tool_result blocks
# ABOUTME: Fixes extractor hard-coding all VERIFY outcomes to false (40/40 events across 4 sessions)

# Harness Change Contract: VERIFY outcome capture from tool_result

## Component

Skill: `skills/harness-trace/` (`src/harness_trace/extractor.py`, `src/harness_trace/models.py`).

## Failure mode targeted

Every tool-signaled VERIFY entry was emitted with hard-coded `{"tests_pass": false, "lint_clean": false, "build_ok": false}` (old extractor.py comment: "Tool-use signal can't tell pass/fail from the call alone; leave defaults"). Observed: 40/40 VERIFY events across sessions 447e00c7, 4525452c, 5b0d9aa4, 15ffb338 report triple-failure, including session 15ffb338 (2026-07-04, ~20 merged PRs, visibly green). A hard-coded false is indistinguishable from a real red run, so stuck-verify loops and flaky tests can never be detected from traces.

## Predicted improvement

Re-extracting a known-green session yields mostly non-false outcomes. Measured on 15ffb338 at implementation time: 25 VERIFY entries, 17 with `tests_pass=true`, 20 with `lint_clean` resolved (18 true, 2 false), 0 fabricated all-false rows. Fields are now tri-state (`true`/`false`/`null`): `null` = unknown (result missing from stream, or command says nothing about that axis).

## Invariants preserved

- Schema stays v2; field names unchanged; extraction stays offline and deterministic.
- No outcome is ever fabricated: a verify call whose tool_result never arrives stays `null` on all axes.
- Failure markers in output (e.g. "3 failed") override a clean exit code (`pytest || true` chains).
- Text-fallback VERIFY parsing (prose "tests pass") unchanged.

## Falsification

Re-extracting a session known to have ended green (e.g. 15ffb338) yields all-false VERIFY entries again, OR a session with a visibly red run in the transcript yields `tests_pass=true` for that run. Either observation over the next 10 extracted sessions → revert.

## Rollback

`git revert` of the commit referencing this contract. Affects: `skills/harness-trace/src/harness_trace/extractor.py`, `src/harness_trace/models.py`, `tests/`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-15 | 5 post-fix sessions (8b9ec97a, 6ca2d622, 539ab00c, c8dad2d3, c95e129a), ~60 VERIFY events | Tri-state outcomes throughout, real red→green cycles visible (e.g. 8b9ec97a), zero fabricated all-false rows; falsification not fired | interim (window is 10 sessions), on track for **kept** |
