# ABOUTME: Harness optimization through execution trace analysis
# ABOUTME: Evidence-based proposals for improving rules, skills, and agent definitions

---
name: harness-mechanic
description: "Harness optimization: analyze execution traces, propose rule/skill improvements. Use when user says optimize harness, harness review, improve rules, meta-harness, or /harness-mechanic. Not for trace capture (use harness-trace)."
---

# Harness Mechanic

Automated harness optimization based on Meta-Harness (arxiv 2603.28052). Reads execution traces and token baselines, identifies systematic failures, proposes evidence-based improvements.

## Quality Notes

- Read ALL available traces before proposing changes
- Quality of analysis matters more than number of proposals
- Every proposal needs trace evidence; no speculation

## Workflow

### On-Demand: `/harness-mechanic`

1. Read latest token baseline: `quality_reports/token_baselines/`
2. Read recent traces: `quality_reports/traces/` (last 10 sessions)
3. Launch harness-mechanic agent with traces + baselines
4. Present proposals for approval
5. If approved: apply changes, then run `/skill-forge review` on modified files

### Prerequisites

| Check | How |
|-------|-----|
| Traces exist | `ls quality_reports/traces/*.jsonl` |
| Baseline exists | `ls quality_reports/token_baselines/*.tsv` |
| No traces? | Run `harness-trace extract` on recent sessions first |
| No baseline? | Run `harness-trace baseline --base-dir .` first |

## When to Run

- Weekly review (e.g., Friday)
- After a milestone week with many orchestrator sessions
- When review loop is stuck (score < 80 after 2+ rounds)
- After noticing recurring failures across sessions

## Common Issues

| Issue | Solution |
|-------|----------|
| No traces available | Extract from session JSONL: `harness-trace extract` |
| All scores high, no patterns | Skip; harness is working well |
| Baseline missing | Run `harness-trace baseline` |
| Proposal seems risky | Always RED decision; reject and ask for alternatives |
| Composite tasks fail but steps look OK | Use cascade analysis: check atomic skill metrics (LOCALIZE precision, REPRODUCE success, review_validity) to find the root skill deficiency |
| Same skill weak across sessions | Target the corresponding orchestrator step or agent prompt, not broad rule changes |
