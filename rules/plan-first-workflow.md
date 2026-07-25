# ABOUTME: Plan before build — refine requirements, save plans to disk, preserve context
# ABOUTME: Mandatory for multi-file changes, new features, architectural decisions

# Plan-First Workflow

## When to Plan

Multi-file changes, new features, integrations, anything 🟡 or 🔴 in decision framework.

## Requirements Refinement (MUST run before planning)

**MANDATORY** for any 🟡/🔴 task. Identify gray areas and clarify with `AskUserQuestion` BEFORE entering plan mode. Skip ONLY for: single-file changes, fully specific instructions, or explicit user skip.

**1. Analyze gray areas** — what decisions would change the implementation?
- Visual feature → layout, density, interactions, empty states
- API/CLI → response format, error handling, auth flow
- Infrastructure → scaling, redundancy, monitoring
- Integration → protocol, auth method, error recovery

**2. Clarify with `AskUserQuestion`** — concrete options, not open-ended
- Options must be specific ("JWT sessions" not "Option A")
- Include "You decide" when Claude's discretion is reasonable

**3. Scope discipline** — clarify HOW, never expand WHAT
- New scope suggested during refinement → capture as "deferred idea", redirect

**4. Capture decisions** — feed into the plan
- Add a `## Decisions` section to the plan file (append-only across sessions)
- Format: `| # | Decision | Choice | Rationale | Revisit if |`
- Never edit/remove rows; to reverse, add a new row that supersedes
- Record: what was decided, why, what was deferred to Claude's discretion

Can also be invoked explicitly via `/refine-requirements`.

## Process

1. Requirements refinement (above) — only for ambiguous requests
2. Plan mode → draft: files, approach, dependencies, verification, risks, budget (below)
3. Save plan: `quality_reports/plans/active/YYYY-MM-DD_<slug>.md` in the working repo — a fresh session can only see what is in the repo. Mirror to vault (`obsidian create name="Plans/YYYY-MM-DD - description" content="..." silent`) for cross-project tracking; the repo copy is the source of truth
4. Approve → orchestrator

## Budget

The plan declares what the run is allowed to spend, before implementation starts. It is the single place these limits live; the loop reads them from here.

| Limit | Default |
|-------|---------|
| Fix rounds (REVIEW→FIX plus UAT→FIX) | 5, then escalate |
| Concurrent write agents | 3 (5 only when file scopes are disjoint) |
| Sub-agents for the whole run | state a number; needing more is a re-plan, not a wider fan-out |
| Minimum evidence to finalize | test/lint/build green after the last source edit |

Raise a default in the plan when the task justifies it, with the reason on the same line. When a limit is reached, stop and return the best current artifact, what is done, what is unresolved, and which limit stopped you. A fluent summary that hides a partial failure is itself the failure.

## Living Plans (ExecPlans)

For complex tasks (research verdict = complex) or work expected to span sessions, the plan is a living document updated DURING execution, not a snapshot. Self-containment test: a fresh session must be able to resume from the plan file alone, without chat history.

Mandatory sections, kept current:

| Section | Content | Updated |
|---------|---------|---------|
| `## Progress` | Timestamped checklist, actual current state | After each subtask |
| `## Surprises & Discoveries` | Unexpected behavior/insights, with evidence (output, diff) | When they happen |
| `## Decisions` | Append-only table (see Requirements Refinement) | Every execution-time decision, not just refinement-time |
| `## Outcomes & Retrospective` | What shipped, gaps, lessons — feeds learning-docs | At close |

The plan's work steps (tracked in `## Progress`) state observable outcomes ("`curl :8080/health` returns 200"), not implementation detail, and are independently verifiable.

Lifecycle (ALL plans, living or not): create in `quality_reports/plans/active/`, move to `quality_reports/plans/completed/` at close — for living plans, with the retrospective filled. Tech debt discovered but not addressed: one line in `quality_reports/plans/tech-debt.md` pointing back to the plan.

## Annotation Cycle (complex only)

Activates when research-analyst verdict = **complex** (see orchestrator-protocol).

1. Save plan as usual
2. Developer adds inline annotations in plan file (terse: "not optional", "use X instead", "remove this")
3. Address ALL annotations, update plan in-place, do NOT implement
4. Repeat 2-3 until approved (1-4 rounds typical)
5. Approved → orchestrator loop

## Checkpoints in Plans

Plans MAY include checkpoint markers (0-2 per plan). Between checkpoints, execution is autonomous.

| Marker | When | Effect |
|--------|------|--------|
| `<!-- checkpoint:verify -->` | After UI, deploy, auth flow | STOP, user verifies |
| `<!-- checkpoint:decide -->` | Architectural fork | STOP, present options, wait |

## Session Logging

Append to project log in vault: `obsidian append file="<project> - Log" content="## YYYY-MM-DD: <goal>\n..."` (fallback: `quality_reports/session_logs/`)

- **Post-plan:** goal, plan summary, key context
- **During:** decisions, problems, review findings (1-3 lines each)
- **End:** accomplishments, open questions

## Context Preservation

When compressing or summarizing session state, regenerate from source files (code, tests, git log), never compress an existing summary. Summaries drift; the codebase is the lossless source of truth.

A `[context-watcher]` nudge (context ≥60% of the compaction window) is a mandatory pause signal: update the living plan's `## Progress` and Next Action, or write `.continue-here.md`, BEFORE continuing the task; auto-compact can fire without further warning. After an auto-compact, the `[compact-resume]` prompt points back to exactly these files.

When pausing mid-task: if a living plan exists (see Living Plans), update its `## Progress` and `## Decisions` sections instead — the plan is the resume point, and it accumulates instead of being deleted. Only for unplanned/simple work, write `.continue-here.md` in the working directory:

```markdown
## Current State
## Completed
## Remaining
## Decisions Made (with WHY — prevents re-debating)
## Next Action (specific enough for a fresh session)
```

Delete after resuming.
