# ABOUTME: Plan before build — save plans to disk, preserve context across compression
# ABOUTME: Mandatory for multi-file changes, new features, architectural decisions

# Plan-First Workflow

## When to Plan

Multi-file changes, new features, integrations, anything 🟡 or 🔴 in decision framework.

## Process

1. Enter plan mode → draft: files, approach, dependencies, verification, risks
2. Save to `quality_reports/plans/YYYY-MM-DD_description.md`
3. Present for approval → implement via orchestrator

## Session Logging

Append to `quality_reports/session_logs/YYYY-MM-DD_description.md`:
- **Post-plan:** goal, plan summary, context
- **During work:** design decisions, problems solved, review findings (1-3 lines)
- **End of session:** accomplishments, open questions

## Context Preservation

NEVER `/clear`. Rely on auto-compression. Save state to disk before context gets large.
