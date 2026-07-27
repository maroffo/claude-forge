# ABOUTME: Change contract: literal LOCALIZE/REPRODUCE/DRIFT report lines + extractor patterns
# ABOUTME: Makes step-1 sub-protocol execution visible in traces (0 events across 12/12 sessions)

# Harness Change Contract: sub-step report formats (LOCALIZE / REPRODUCE / DRIFT)

## Component

- Rule: `rules/orchestrator-protocol.md`, Sub-protocols section: mandated one-line report formats.
- Skill: `skills/harness-trace/` (`src/harness_trace/extractor.py` patterns, `models.py` LocalizeData count fields, `tests/test_extractor.py`).

## Failure mode targeted

Step-1 sub-protocol execution (LOCALIZE 1a, REPRODUCE 1b, DRIFT 1c) is unobservable in telemetry: 0 events across 12/12 traced sessions (2026-06-08 → 2026-07-10), including the 140-file session 15ffb338. The protocol defines trace data for these steps but mandates no report format, and the extractor has no patterns for them, so "skipped" and "performed but unparseable" are indistinguishable. Same ambiguity the 2026-07-05 score-report-format contract removed for SCORE (0 → 9 events after mandating a literal line). Cascade analysis (harness-mechanic) needs LOCALIZE precision and REPRODUCE success; both are currently uncomputable.

## Predicted improvement

Next 5 non-SKIP_SET multi-file orchestrator sessions emit ≥1 LOCALIZE event each; bug-fix sessions emit a REPRODUCE event; multi-subtask sessions emit DRIFT_CHECK events. If events still do not appear, the diagnosis shifts cleanly to "the sub-steps are being skipped", actionable via a different contract (mirrors the SCORE precedent).

## Invariants preserved

- Schema stays v2; LocalizeData gains only optional additive fields (`planned_count`, `proposed_count`); all existing traces still parse.
- No fabricated events: prose mentioning "localize"/"reproduce"/"drift" without the literal key=value shape emits nothing (tested); a partial line missing mandated fields emits nothing (tested).
- Existing step extraction unchanged: full suite green (99 tests).
- Always-on token cost of the rule grows by ~7 lines only.

## Falsification

Over the next 10 extracted sessions: spurious LOCALIZE/REPRODUCE/DRIFT_CHECK events extracted from ordinary prose (false positive), OR a transcript visibly containing the mandated literal line that extracts no event (extractor miss). Either → revert.

## Rollback

Shared commit with 2026-07-15_blast-radius-report-keyed.md; selective rollback: remove the three sub-step STEP_PATTERNS rows, the three `_extract_text_step_data` branches, the LOCALIZE/REPRODUCE/DRIFT report patterns and text-eligibility entries in `extractor.py`, the `planned_count`/`proposed_count` fields in `models.py`, and the "Report each executed sub-step" block in `rules/orchestrator-protocol.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions, of which 4 post-fix with more than 3 changed files | insufficient data: LOCALIZE, REPRODUCE and DRIFT_CHECK are all 0 across the whole corpus, and the falsifier cannot be evaluated because it needs a transcript that visibly contains a mandated line, which the extracted traces do not include; the false-positive arm did not fire (0 events means 0 spurious events); re-check by extracting the 2026-07-27 swarm-forge session, which emitted 3 DRIFT lines live, and confirming 3 DRIFT_CHECK events appear | kept |
