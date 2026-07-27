# ABOUTME: Trace Schema (v2) taxonomy, JSONL structure, metrics, and harness-trace architecture
# ABOUTME: Read when analyzing trace schema v2 fields or understanding harness-trace internal architecture

## Trace Schema (v2)

One JSONL line per orchestrator step. `v2` adds `rejected_alternatives` (top-level, attaches to any step), two new step types (`PERMISSION_EVENT`, `ROUTE`), and an end-of-task `metrics` mini-report inside `SUMMARY`. Based on "Code as Agent Harness" (arxiv 2605.18747 §3.5.1, §5.2.1).

**Step taxonomy.** `step` mixes two kinds intentionally:
- **Lifecycle phases** (`REFINE`, `RESEARCH`, ..., `SUMMARY`): at most once per round, sequential.
- **Cross-cutting events** (`PERMISSION_EVENT`, `ROUTE`): fire opportunistically, possibly many per phase. Consumers that care about the distinction should filter by step name.

```jsonl
{"v":2,"session":"slug","ts":"ISO8601","step":"STEP","data":{...},"rejected_alternatives":[...]}
```

| Step | Data fields |
|------|-------------|
| REFINE | ambiguities_found, questions_asked |
| RESEARCH | complexity, sources_consulted |
| LOCALIZE | files_planned, files_proposed, files_actually_changed, planned_count, proposed_count, precision, recall (tri-state: null = not reported), mismatches |
| REPRODUCE | script, fails_before_fix, passes_after_fix |
| IMPLEMENT | agents, files_changed, subtask_count, localization_precision |
| DRIFT_CHECK | subtask_id, verdict, deviations |
| VERIFY | tests_pass, lint_clean, build_ok (each tri-state: true/false/null, null = unknown), retries, reproduction_confirmed |
| REVIEW | agents, findings (CRITICAL/MAJOR/MINOR), review_validity |
| FIX | findings_addressed, deviations |
| BLAST_RADIUS | triggered, trigger_reason, files_scanned, contradictions |
| SCORE | score, threshold, gate |
| LOOP | round, total_rounds, exit_reason |
| UAT | performed, items, passed, failed |
| SUMMARY | tokens_in/out, model, duration, final_score, **metrics** (v2) |
| **PERMISSION_EVENT** (v2) | tool, action, outcome (granted/denied/denied_by_settings/auto_approved/error/timeout/bypassed), reason. Callers must redact secrets in `action`. |
| **ROUTE** (v2) | router, target, alternatives_considered, decision_basis |
| **EXECUTOR** (v2) | executor, model, subtask_id |
| **REVIEW_ARTIFACT** (v2) | round, path, findings (CRITICAL/MAJOR/MINOR counts), converged |

### v2 cross-cutting fields

- `rejected_alternatives` (top-level on TraceEntry): list of `{description, reason_rejected, cost_estimate?}`. Captures paths the agent considered but discarded. Useful for diagnosing decision quality without rerunning the agent.

### v2 SUMMARY.metrics (6 harness dimensions, paper §5.2.1)

Each dimension is an optional dict; populate only what was measured. `None` = not measured (do not infer 0).

| Dimension | Suggested keys |
|-----------|----------------|
| trajectory_efficiency | tool_calls, tokens, edits, executions, active_min (gap-clamped working time, paired with SUMMARY.duration_min calendar span) |
| verification_strength | test_coverage_pct, oracles_count, false_accept_rate |
| recovery_ability | failures, recovered, escalations |
| state_consistency | memory_repo_synced, drift_detected |
| safety_compliance | permission_denials, hitl_gates_hit, sandbox_used |
| replayability | full_trace_captured, artifacts_persisted |

## Architecture

```
src/harness_trace/
  models.py         <- Pydantic trace schema (TraceEntry, step data models)
  extractor.py      <- Session JSONL -> trace JSONL (heuristic parser)
  token_counter.py  <- tiktoken counting, directory scanning, TSV generation
  cli.py            <- CLI entry point (extract, count-tokens, baseline)
tests/              <- pytest suite
```
