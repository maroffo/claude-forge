# ABOUTME: Change contract for the EXECUTOR literal-line event type in the harness-trace extractor
# ABOUTME: Additive telemetry: makes pi-executed subtasks countable in traces without grep

# Harness Change Contract: EXECUTOR event type in harness-trace

## Component

`skills/harness-trace` internals: `src/harness_trace/extractor.py` (EXECUTOR_REPORT_PATTERN + LITERAL_REPORT_STEPS wiring), `src/harness_trace/models.py` (StepName + ExecutorData + STEP_DATA_MODELS), `tests/test_extractor.py`, `SKILL.md` body docs. Trigger surface (frontmatter description) untouched.

## Failure mode targeted

The Executor selection rule (rules/orchestrator-protocol.md, PR #96) mandates the literal transcript line `EXECUTOR: pi-exec model=<id> subtask=<id>`, but the extractor's LITERAL_REPORT_STEPS knew only LOCALIZE/REPRODUCE/DRIFT/BLAST-RADIUS: pi-executed subtasks were invisible in traces, and the pi-flash-executor contract's falsification metric had to be counted by hand with grep (issue #95).

## Predicted improvement

EXECUTOR events appear as first-class steps in extracted traces; the pi-flash-executor pilot (first 5 pi-executed subtasks) is countable via `harness-trace extract` alone, zero grep. Sample: the next 5 traced sessions that use pi-exec.

## Invariants preserved

- SCHEMA_VERSION unchanged; every previously-parsing trace still parses (additive StepName only).
- Existing step extraction untouched (full 109-test suite green, no sibling pattern modified).
- Fenced-code-block stripping still prevents quoted lines from forging events (non-forgery test added for EXECUTOR).

## Falsification

Any previously-parsing session trace fails to parse after this change, or an EXECUTOR event is emitted from quoted/fenced text or tool output rather than an orchestrator transcript line. Either observation: revert.

## Rollback

`git revert <commit>`. Affects: skills/harness-trace/src/harness_trace/extractor.py, skills/harness-trace/src/harness_trace/models.py, skills/harness-trace/tests/test_extractor.py, skills/harness-trace/SKILL.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
