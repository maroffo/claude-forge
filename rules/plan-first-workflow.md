# ABOUTME: Plan before build — save plans to disk, preserve context across compression
# ABOUTME: Mandatory for multi-file changes, new features, architectural decisions

# Plan-First Workflow

## When to Plan

- Multi-file changes (>3 files)
- New features or integrations
- Architectural decisions
- Anything rated 🟡 or 🔴 in the decision framework

## Process

1. **Enter plan mode** for non-trivial tasks
2. **Draft plan**: files to change, approach, dependencies, verification steps, risks
3. **Save to disk**: `quality_reports/plans/YYYY-MM-DD_description.md`
4. **Present for approval** — wait for explicit go-ahead
5. **Implement via orchestrator** (see orchestrator-protocol)

## Plan Persistence

Plans saved to disk survive context window compression. Always save before implementing.

```
quality_reports/
├── plans/              # Implementation plans
└── session_logs/       # Session history and decisions
```

## Session Logging

- **Post-plan**: Save goal, plan summary, context, rationale
- **During work**: Append 1-3 lines for design decisions, problems solved, review findings
- **End of session**: Accomplishments, open questions, unresolved issues

Location: `quality_reports/session_logs/YYYY-MM-DD_description.md`

## Context Preservation

- NEVER use `/clear` — rely on auto-compression
- Save state to disk before context gets large
- Reference saved plans/logs when resuming work
