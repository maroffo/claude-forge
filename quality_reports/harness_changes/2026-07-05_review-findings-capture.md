# ABOUTME: Change contract: REVIEW entries capture severity counts from the reviewer's tool_result
# ABOUTME: Fixes extractor hard-coding findings to {} for every reviewer Agent call (12/12 events)

# Harness Change Contract: REVIEW findings capture from reviewer reports

## Component

Skill: `skills/harness-trace/` (`src/harness_trace/extractor.py`).

## Failure mode targeted

Every tool-signaled REVIEW entry was emitted with hard-coded `findings: {}`; the reviewer's actual report (returned in the Agent call's tool_result) was never parsed. Observed: 12/12 REVIEW events across sessions 4525452c, 5b0d9aa4, 15ffb338 carry empty findings, making `review_validity` permanently uncomputable and reviewer token cost unmeasurable against returned value (paper 2605.18747 §3.5.1).

## Predicted improvement

Findings populated whenever the reviewer output reaches the tool_result in one of two recognized formats: explicit counts ("MAJOR: 1") or section-style reports ("### MAJOR" + one bullet per finding). Measured at implementation time: 8 of 8 synchronous reviewer results across the 3 traced sessions now yield counts (e.g. 15ffb338 dx-reviewer: CRITICAL 0, MAJOR 4, MINOR 4); async-launched reviewers (metadata-only tool_result) correctly stay `{}`.

## Invariants preserved

- Findings are never fabricated: unparseable or missing reports leave `{}`.
- Schema stays v2; `ReviewData.findings` shape unchanged (severity -> count).
- errored Agent results are ignored (no counts from failure messages).
- ROUTE emission and reviewer/non-reviewer distinction unchanged.

## Falsification

A session whose reviewer report visibly contains severity counts (either format) still extracts `{}`, OR a non-review text (e.g. prose mentioning "critical issue") produces nonzero findings. Either observation over the next 10 extracted sessions → revert.

## Rollback

`git revert` of the commit referencing this contract. Affects: `skills/harness-trace/src/harness_trace/extractor.py`, `tests/`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
