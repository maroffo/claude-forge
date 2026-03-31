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

## Trace Schema (v1)

One JSONL line per orchestrator step:

```jsonl
{"v":1,"session":"slug","ts":"ISO8601","step":"STEP","data":{...}}
```

| Step | Data fields |
|------|-------------|
| REFINE | ambiguities_found, questions_asked |
| RESEARCH | complexity, sources_consulted |
| IMPLEMENT | agents, files_changed, subtask_count |
| VERIFY | tests_pass, lint_clean, build_ok, retries |
| REVIEW | agents, findings (CRITICAL/MAJOR/MINOR) |
| FIX | findings_addressed, deviations |
| SCORE | score, threshold, gate |
| LOOP | round, total_rounds, exit_reason |
| UAT | performed, items, passed, failed |
| SUMMARY | tokens_in/out, model, duration, final_score |

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
