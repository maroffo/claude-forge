# ABOUTME: Structured execution trace capture and token baselining for claude-forge
# ABOUTME: Extracts traces from session JSONL, counts tokens with tiktoken, generates baselines

---
name: harness-trace
description: "Execution trace capture and token baselining. Use when user says trace, extract trace, count tokens, token baseline, or /harness-trace. Not for harness optimization (use harness-mechanic)."
compatibility: "Python >=3.11, uv"
---

# Harness Trace

Structured execution trace capture and token baselining for the claude-forge harness. Based on Meta-Harness (arxiv 2603.28052): measure before optimizing.

## Quick Start

```bash
cd skills/harness-trace

# Install
uv sync

# Extract traces from a session JSONL
uv run -- harness-trace extract ~/.claude/projects/PROJECT/SESSION.jsonl

# Count tokens in harness files
uv run -- harness-trace count-tokens rules/

# Generate full baseline
uv run -- harness-trace baseline --base-dir /path/to/claude-forge
```

## Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `extract <session.jsonl>` | Parse session into trace JSONL | Trace entries (stdout or file) |
| `count-tokens <path>` | Count tokens per file | Token counts per file |
| `baseline --base-dir <dir>` | Full harness token baseline | TSV with tier classification |

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
| LOCALIZE | files_planned, files_proposed, files_actually_changed, precision, recall, mismatches |
| REPRODUCE | script, fails_before_fix, passes_after_fix |
| IMPLEMENT | agents, files_changed, subtask_count, localization_precision |
| DRIFT_CHECK | subtask_id, verdict, deviations |
| VERIFY | tests_pass, lint_clean, build_ok, retries, reproduction_confirmed |
| REVIEW | agents, findings (CRITICAL/MAJOR/MINOR), review_validity |
| FIX | findings_addressed, deviations |
| BLAST_RADIUS | triggered, trigger_reason, files_scanned, contradictions |
| SCORE | score, threshold, gate |
| LOOP | round, total_rounds, exit_reason |
| UAT | performed, items, passed, failed |
| SUMMARY | tokens_in/out, model, duration, final_score, **metrics** (v2) |
| **PERMISSION_EVENT** (v2) | tool, action, outcome (granted/denied/denied_by_settings/auto_approved/error/timeout/bypassed), reason. Callers must redact secrets in `action`. |
| **ROUTE** (v2) | router, target, alternatives_considered, decision_basis |

### v2 cross-cutting fields

- `rejected_alternatives` (top-level on TraceEntry): list of `{description, reason_rejected, cost_estimate?}`. Captures paths the agent considered but discarded. Useful for diagnosing decision quality without rerunning the agent.

### v2 SUMMARY.metrics (6 harness dimensions, paper §5.2.1)

Each dimension is an optional dict; populate only what was measured. `None` = not measured (do not infer 0).

| Dimension | Suggested keys |
|-----------|----------------|
| trajectory_efficiency | tool_calls, tokens, edits, executions, wall_clock_min |
| verification_strength | test_coverage_pct, oracles_count, false_accept_rate |
| recovery_ability | failures, recovered, escalations |
| state_consistency | memory_repo_synced, drift_detected |
| safety_compliance | permission_denials, hitl_gates_hit, sandbox_used |
| replayability | full_trace_captured, artifacts_persisted |

## Token Baseline TSV

```
file	tokens	words	lines	tier	loaded
rules/orchestrator-protocol.md	1247	450	67	rule	always
skills/golang/SKILL.md	2890	1050	145	skill	on-demand
```

Tiers: `rule` (always-on), `skill`/`skill-ref` (on-demand), `agent` (on-demand), `config` (always-on).

## Architecture

```
src/harness_trace/
  models.py         <- Pydantic trace schema (TraceEntry, step data models)
  extractor.py      <- Session JSONL -> trace JSONL (heuristic parser)
  token_counter.py  <- tiktoken counting, directory scanning, TSV generation
  cli.py            <- CLI entry point (extract, count-tokens, baseline)
tests/              <- pytest suite
```
