# ABOUTME: Plan before build — refine requirements, save plans to disk, preserve context
# ABOUTME: Mandatory for multi-file changes, new features, architectural decisions

# Plan-First Workflow

## When to Plan

Multi-file changes, new features, integrations, anything 🟡 or 🔴 in decision framework.

## Requirements Refinement (MUST run before planning)

**MANDATORY** for any 🟡/🔴 task. BEFORE entering plan mode, identify gray areas and clarify with `AskUserQuestion`. Do NOT draft a plan with unresolved ambiguities.

Skip ONLY when: single-file change, user gave fully specific instructions, or user explicitly says to skip.

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
- Add a `## Decisions` section to the plan file
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

Plans MAY include checkpoint markers for moments where human judgment matters.

| Marker | When to use | Effect |
|--------|-------------|--------|
| `<!-- checkpoint:verify -->` | After UI, deploy, auth flow | STOP, show what was built, ask user to verify |
| `<!-- checkpoint:decide -->` | Architectural fork during execution | STOP, present options with trade-offs, wait |

Between checkpoints, execution is autonomous. Use sparingly: 0-2 per plan.

## Session Logging

Append to project log in vault: `obsidian append file="<project> - Log" content="## YYYY-MM-DD: <goal>\n..."` (fallback: `quality_reports/session_logs/`)

- **Post-plan:** goal, plan summary, key context
- **During:** decisions, problems, review findings (1-3 lines each)
- **End:** accomplishments, open questions

## Context Preservation

When pausing mid-task or before context gets large, write `.continue-here.md` in the working directory:

```markdown
## Current State
## Completed
## Remaining
## Decisions Made (with WHY — prevents re-debating)
## Next Action (specific enough for a fresh session)
```

Delete after resuming.
