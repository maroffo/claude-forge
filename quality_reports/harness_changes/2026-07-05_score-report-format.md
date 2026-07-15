# ABOUTME: Change contract: mandate literal "SCORE: <n>/100" reporting format in step 6
# ABOUTME: Makes quality-gate scoring visible to the harness-trace extractor (0 SCORE events in 6 sessions)

# Harness Change Contract: standardize step 6 score reporting format

## Component

Rule: `rules/orchestrator-protocol.md`, new "Score Reporting (Step 6)" section.

## Failure mode targeted

0 SCORE events across all 6 traced sessions (2026-06-08 through 2026-07-04), despite quality-gates.md mandating scoring before every commit. The extractor's text pattern (`score:\s*<n>`) exists and works (unit-tested), so either scoring is skipped or reported in unmatchable free-form phrasing; the two are indistinguishable in telemetry. This contract removes the phrasing ambiguity so the residual signal (still no SCORE events = scoring actually skipped) becomes interpretable.

## Predicted improvement

Orchestrator sessions that run step 6 emit ≥1 SCORE trace event. Detection sample: next 5 orchestrator (non-SKIP_SET) sessions. Secondary effect: if events still do not appear, the diagnosis shifts cleanly to "scoring is being skipped", actionable via a different contract.

## Invariants preserved

- No extractor code change: the existing `SCORE_PATTERN` already matches the mandated format.
- Scoring rubric, thresholds, and gates unchanged (quality-gates.md untouched).
- No new step added to the loop; only the output format of an existing step.

## Falsification

After 5+ orchestrator sessions post-change: SCORE events still absent while the transcript visibly contains step 6 score reports in the mandated format (extractor miss), OR sessions start emitting spurious SCORE events from non-step-6 prose. Either → revert.

## Rollback

`git revert` of the commit referencing this contract. Affects: `rules/orchestrator-protocol.md` (single section removal).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-15 | 5 post-change orchestrator sessions (the contract's stated detection sample) | 5/5 emit ≥1 SCORE event, 11 events total (scores 84–100); zero spurious SCORE events from non-step-6 prose | **kept** |
