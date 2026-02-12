# ABOUTME: Plan before build — save plans to disk, preserve context across compression
# ABOUTME: Mandatory for multi-file changes, new features, architectural decisions

# Plan-First Workflow

## When to Plan

Multi-file changes, new features, integrations, anything 🟡 or 🔴 in decision framework.

## Process

1. Plan mode → draft: files, approach, dependencies, verification, risks
2. Save to `quality_reports/plans/YYYY-MM-DD_description.md`
3. Approve → orchestrator

## Annotation Cycle (complex only)

Activates when research-analyst verdict = **complex** (see orchestrator-protocol).

1. Save plan as usual
2. Developer adds inline annotations in plan file (terse: "not optional", "use X instead", "remove this")
3. Address ALL annotations, update plan in-place, do NOT implement
4. Repeat 2-3 until approved (1-4 rounds typical)
5. Approved → orchestrator loop

## Session Logging

Append to `quality_reports/session_logs/YYYY-MM-DD_description.md`:
- **Post-plan:** goal, plan summary, key context
- **During:** decisions, problems, review findings (1-3 lines each)
- **End:** accomplishments, open questions

## Context Preservation

Rely on auto-compression. Save state to disk before context gets large.
