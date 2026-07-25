---
name: harness-trace
description: "Execution trace capture and token baselining. Use when user says trace, extract trace, count tokens, token baseline, or /harness-trace. Not for harness optimization (use harness-mechanic)."
compatibility: "Python >=3.11, uv"
---

# ABOUTME: Structured execution trace capture and token baselining for claude-forge
# ABOUTME: Extracts traces from session JSONL, counts tokens with tiktoken, generates baselines

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

## Extraction strategy

`extract` uses three signal sources, in order of precision:

1. **Tool-use blocks** (primary, high precision). Walks every `tool_use` block in the assistant messages, then resolves outcomes from the paired `tool_result` blocks (matched by `tool_use_id`) in the user messages:

   | Tool / pattern | Emits |
   |----------------|-------|
   | `Agent(subagent_type=*-reviewer)` | `ROUTE` + `REVIEW`; findings parsed from the reviewer's returned report (section-style `### MAJOR` + one bullet per finding, or explicit `MAJOR: 1` counts) |
   | `Agent(subagent_type=*)` (non-reviewer) | `ROUTE` |
   | `Bash` matching `pytest\|make test\|go test\|npm test\|cargo test\|rspec` | `VERIFY`, `tests_pass` resolved from the result |
   | `Bash` matching `make check` | `VERIFY`, `lint_clean` resolved from the result |
   | `Edit` / `Write` / `MultiEdit` | counted into `IMPLEMENT` aggregate |
   | `WebFetch` to `arxiv\|docs` | `RESEARCH` |
   | `AskUserQuestion` | counted into `safety_compliance.hitl_gates_hit` |

   Outcome resolution is fail-safe: a result that never arrives (truncated session, async agent) or says nothing about an axis leaves it unknown; failure markers in output override a clean exit (`pytest || true` chains); counts are never fabricated from prose.

2. **Literal report lines** (exact formats mandated by `rules/orchestrator-protocol.md`): `LOCALIZE: planned=… proposed=…` → `LOCALIZE`, `REPRODUCE: script=… fails_before_fix=…` → `REPRODUCE`, `DRIFT: subtask=… verdict=…` → `DRIFT_CHECK`, `BLAST-RADIUS: clean|MAJOR=n MINOR=m|skipped (…)` → `BLAST_RADIUS`, `EXECUTOR: <executor> model=<id> subtask=<id>` → `EXECUTOR`. Detection and extraction share one compiled pattern per step; lines are checked independently per message (the protocol co-locates them). `BLAST_RADIUS` is keyed ONLY on this line: ast-grep usage is not a signal (the always-use-sg rule saturated it). Fenced code blocks are stripped first so quoted lines cannot forge events.

3. **Text regex** (fallback prose heuristics). Applied only to messages whose tool stream did not already surface the step, and only for steps that are typically pure text (`SCORE`, `FIX`, `LOOP`, `UAT`, plus `VERIFY`/`REVIEW` when no tool signal exists). This avoids the v1 problem where prose like "tests pass" in a chat triggered fake VERIFY entries.

`SUMMARY` is always synthesized last from JSONL aggregates: `duration_min` (last_ts - first_ts), `files_changed` (Edit+Write count), and the 6-dimension `metrics` object (paper §5.2.1). No `SUMMARY` is emitted for sessions with zero other entries.

## Trace Schema (v2)

See `references/schema.md`.

## Token Baseline TSV

```
file	tokens	words	lines	tier	loaded
rules/orchestrator-protocol.md	1247	450	67	rule	always
skills/golang/SKILL.md	2890	1050	145	skill	on-demand
```

Tiers: `rule` (always-on), `skill`/`skill-ref` (on-demand), `agent` (on-demand), `config` (always-on).

## Common Issues

See `references/troubleshooting.md`.

## Architecture

See `references/schema.md`.
