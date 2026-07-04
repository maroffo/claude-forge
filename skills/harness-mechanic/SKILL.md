---
name: harness-mechanic
description: "Harness optimization: analyze execution traces, propose rule/skill improvements. Use when user says optimize harness, harness review, improve rules, meta-harness, or /harness-mechanic. Not for trace capture (use harness-trace)."
---

# ABOUTME: Harness optimization through execution trace analysis
# ABOUTME: Evidence-based proposals for improving rules, skills, and agent definitions

# Harness Mechanic

An *Evolution Agent* (paper §3.5.2 of arxiv 2605.18747 "Code as Agent Harness") for the claude-forge runtime. Reads execution traces, token baselines, and prior change contracts; proposes evidence-backed edits to `hooks/`, `rules/`, `skills/`, and `agents/`.

## Prior art (load-bearing references)

- **Meta-Harness** (arxiv 2603.28052): outer-loop search over harness code via an agentic proposer that reads source, scores, and traces of all prior candidates from a filesystem. Reported +7.7 pts on text classification with 4× fewer context tokens, +4.7 on IMO problems, beats hand-engineered TerminalBench-2 baselines. The proposer-with-filesystem-access pattern is our blueprint: `quality_reports/traces/`, `quality_reports/token_baselines/`, and `quality_reports/harness_changes/` ARE that filesystem.
- **AutoHarness** (arxiv 2603.03329): iterative refinement of code harnesses from environment feedback. Less directly applicable (their domain is games, ours is text/orchestrator), but the principle (smaller-model + synthesized harness beats larger model) is the upper bound we're chasing.
- **Code as Agent Harness** (arxiv 2605.18747) §3.5: defines the 5-stage Evolution Agent loop this skill implements.

## The 5-stage loop (paper §3.5.2)

| # | Stage | What this skill does |
|---|-------|----------------------|
| 1 | **Observe** | Read trace JSONL (`quality_reports/traces/`, schema v2; see `harness-trace`). Read token baseline TSV. Read prior change contracts (`quality_reports/harness_changes/`) for context on what's already been tried. |
| 2 | **Diagnose** | Attribute cost/latency/invalid-actions/test-failures/permission-denials to specific harness components. Cluster across sessions: a failure mode in 1 trace is anecdote; in 5+, it's a pattern. |
| 3 | **Propose** | Concrete edit: rewrite tool description, change context-packing rule, add a linter, modify retry limit, insert HITL gate, adjust routing pattern. Every proposal must carry a draft *change contract* (see `quality_reports/harness_changes/TEMPLATE.md`). |
| 4 | **Evaluate** | Replay against held-out traces if available; otherwise propose the smallest measurement that would falsify (matches the contract's Falsification field). DO NOT promote unverified mutations. |
| 5 | **Promote** | Only after user approval AND a populated change contract. Apply via standard skill edit flow. The contract's Result section gets filled in 10–20 sessions later. |

## Quality bar

- **Read ALL available traces** before proposing. Anecdotal sampling produces vibes-based tweaks.
- **One change = one failure mode** (mirrors the change-contract rule). Bundling makes falsification ambiguous.
- **Evidence or silence.** Every proposal carries trace line numbers / session IDs. No speculation.
- **Telemetry-only failures (cost, latency, denials) are first-class targets**, not just task failures. Paper §3.5.1: "token-cost traces reveal when retrieval or reflection stages consume budget without improving verification outcomes."

## Workflow

### On-demand: `/harness-mechanic`

1. Read latest token baseline: `quality_reports/token_baselines/`
2. Read recent traces: `quality_reports/traces/` (last 10 sessions minimum)
3. Read prior contracts: `quality_reports/harness_changes/*.md` (avoid re-proposing the same change)
4. Run the 5-stage loop above
5. Present proposals + draft change contracts for approval
6. If approved: apply changes, copy draft contract into `quality_reports/harness_changes/`, then run `/skill-forge review` on modified skills

### Prerequisites

| Check | How |
|-------|-----|
| Traces exist | `ls quality_reports/traces/*.jsonl` |
| Schema is v2 | Latest traces should have `"v":2` (see `harness-trace` SKILL.md) |
| Baseline exists | `ls quality_reports/token_baselines/*.tsv` |
| No traces? | Run `harness-trace extract` on recent sessions first |
| No baseline? | Run `harness-trace baseline --base-dir .` first |

## Governance (paper §3.5.3)

This skill is itself subject to the PEV (plan-execute-verify) loop. Treat every proposal as a code change to a safety-critical runtime:

- Changes to **permission boundaries, network access, credential handling, or hook behavior** → require HITL approval before activation. No exceptions.
- Changes to **prompt/instruction text** → can proceed with normal review, but still need a change contract.
- Changes that **expand the permission surface** (e.g. relax a deny rule, broaden an allowlist) → 🔴 always, contract mandatory.

## When to run

- Weekly review (e.g. Friday end-of-day).
- After a milestone week with many orchestrator sessions.
- When the review loop is stuck (score < 80 after 2+ rounds across multiple tasks, not just one).
- After noticing recurring failure patterns across sessions.

## Common issues

| Issue | Action |
|-------|--------|
| No traces available | Extract from session JSONL: `harness-trace extract` |
| Fewer than 5 sessions of traces | Defer: sample too small, retry next week. |
| All scores high, no patterns | Skip; harness is working well. Note this in a short log entry. |
| Baseline missing | Run `harness-trace baseline` |
| Proposal seems risky | 🔴 by default; reject and ask for alternatives. |
| Composite tasks fail but steps look OK | Use cascade analysis: check atomic skill metrics (LOCALIZE precision, REPRODUCE success, review_validity) to find the root skill deficiency. |
| Same skill weak across sessions | Target the corresponding orchestrator step or agent prompt, not broad rule changes. |
| Token cost regression with no quality gain | Paper §3.5.1: this is a first-class signal. Likely retrieval/reflection bloat; propose a context-packing rule. |
