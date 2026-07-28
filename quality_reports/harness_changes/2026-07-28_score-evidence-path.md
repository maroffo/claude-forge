# ABOUTME: Change contract — the SCORE literal gains an optional evidence path, synced across hook/rule/extractor/score-log
# ABOUTME: One failure mode: SCORE events carry no machine-checkable link to their evidence

# Harness Change Contract: SCORE literal carries an evidence-bundle path

## Component

Rule `rules/orchestrator-protocol.md` (SCORE literal), hook `hooks/score-evidence-guard.py` (SCORE_RE recognizes the new form), skill `skills/harness-trace` (`extractor.py` SCORE step, `models.py` ScoreData.evidence_path), script `scripts/score-log.sh` (optional `--evidence` field). The filesystem validation of the path is a separate contract (2026-07-28_score-guard-fs-validation.md); this one covers only the literal and its propagation.

## Failure mode targeted

A `SCORE:` line is a claim with no machine-checkable link to the artifacts that back it: telemetry records score/threshold/gate but nothing connects the event to the test/lint junit and metadata that justified it, so an audited session cannot distinguish an evidence-backed score from an asserted one (real-evidence-pipeline plan, decision 8).

## Predicted improvement

Sessions on repos with `make evidence` emit `SCORE: <n>/100 (threshold: <t>, gate: <g>, evidence: <path>)`; harness traces and score-history.jsonl carry the path. Measurable: fraction of SCORE events in traces with a non-empty evidence_path goes from 0 to >0 on wasit-pilot sessions; stage B (field mandatory for `gate: pr`) is a later, separate change.

## Invariants preserved

- Backward compatible: the evidence field is optional (stage A); the bare literal keeps matching in all four consumers, old score-history rows stay valid (additive JSONL field).
- score-history.jsonl remains a denormalized view of trace SCORE events (score-history contract 2026-07-27): both gain the same field in the same change.
- The trace extractor never fails on a SCORE line without evidence.

## Falsification

Traced sessions show SCORE lines with an evidence path that the extractor drops or mis-parses (trace ScoreData.evidence_path empty while the transcript line carries one); or the hook stops recognizing legacy bare SCORE lines (pre-change sessions would silently lose the two-confirmation gate).

## Rollback

Revert the regex/field additions in the four files; the bare literal is a strict subset of the new form, so no data migration is needed.

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
