# ABOUTME: Change contract: BLAST_RADIUS keyed on a literal step-5b report line, not ast-grep usage
# ABOUTME: The always-use-sg rule saturated the tool signal (15 FP-shaped events in one session, 0 where 5b triggered)

# Harness Change Contract: BLAST_RADIUS re-keyed on explicit report line

## Component

- Rule: `rules/orchestrator-protocol.md`, Blast Radius (step 5b): mandated `BLAST-RADIUS:` report/skip line.
- Skill: `skills/harness-trace/` (`src/harness_trace/extractor.py`: BLAST_BASH_PATTERNS tool-signal removed, literal-line patterns added; `tests/test_extractor.py`; `SKILL.md` extraction-strategy docs synced).

## Failure mode targeted

BLAST_RADIUS telemetry cannot audit step 5b because the extractor fired on any ast-grep invocation while the global code-search rule mandates ast-grep for all searches. Observed: session 6ca2d622 emitted 15 BLAST_RADIUS events, all reason "ast-grep invoked" (ordinary searches); sessions where the >3-files trigger clearly held (15ffb338 with 140 files, c95e129a with 48, 539ab00c with 59) emitted 0. Precision unknown, recall effectively zero.

## Predicted improvement

BLAST_RADIUS events correspond 1:1 with actual step-5b runs or explicit skips. Over the next 5 non-SKIP_SET sessions with >3 changed files, each emits ≥1 BLAST_RADIUS event (report or skip), and no session emits events from ordinary code searches.

## Invariants preserved

- Schema stays v2; BlastRadiusData shape unchanged (triggered, trigger_reason, files_scanned, contradictions).
- Other tool-signaled steps (VERIFY, REVIEW, ROUTE, RESEARCH) and commit counting untouched.
- No event without the literal line: prose mentioning "blast radius" or ast-grep commands emits nothing (tested).
- Full suite green (103 tests).

## Falsification

Over the next 10 extracted sessions: a transcript where step 5b visibly ran (or was explicitly skipped) extracts 0 BLAST_RADIUS events (format unfollowed or extractor miss), OR events appear from non-5b prose. Either → revert.

## Rollback

Shared commit with 2026-07-15_substep-report-formats.md; selective rollback: restore `BLAST_BASH_PATTERNS` and its `elif` branch in `_process_tool_use`, remove the `BLAST_RADIUS` STEP_PATTERNS row, text-eligibility entry, `_extract_text_step_data` branch, and the two rule sentences in the Blast Radius section.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
