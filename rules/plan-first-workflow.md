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
2. Plan mode → draft: files, approach, dependencies, verification, risks
3. Save plan: `obsidian create name="Plans/YYYY-MM-DD - description" content="..." silent` (fallback: `quality_reports/plans/`)
4. Approve → orchestrator

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

When pausing mid-task or before context gets large, write `.continue-here.md` in the working directory:

```markdown
## Current State
## Completed
## Remaining
## Decisions Made (with WHY — prevents re-debating)
## Next Action (specific enough for a fresh session)
```

Delete after resuming.
