---
name: adr
description: "Write Architecture Decision Records following HikmaAI format. Use when user says write ADR, architecture decision, ADR, or decision record. Orchestrates refinement, research, writing, vault storage, and review. Not for implementation plans (use plan mode) or retrospectives (use learning-docs)."
---

# ABOUTME: Full ADR lifecycle: Linear ticket, branch, write, vault, review, commit, PR
# ABOUTME: Follows HikmaAI format and ADR guidelines (Linear ticket = ADR number)

# Architecture Decision Records

## Quality Notes

- Take your time with research before writing
- ADRs are permanent records; accuracy matters more than speed
- Every claim should be backed by evidence (code, docs, benchmarks)
- Do not skip the refinement step for ambiguous topics

## Workflow

### Step 1: Refine Requirements

Before writing, clarify scope using `AskUserQuestion`:

- What decision is being made? (single clear question)
- What options are on the table?
- What constraints apply?
- Who are the stakeholders?

Skip if user provided a fully specified request or said "just write it."

### Step 2: Research

Launch `research-analyst` agent to gather:

- Prior art (existing ADRs in vault, LEARNING.md, MEMORY.md)
- External references (competing approaches, industry patterns)
- Current codebase state (relevant files, existing patterns)

For HikmaAI projects, always check:
- Vault: `Projects/HikmaAI/HLD/` for existing ADRs
- CLAUDE.md for architecture context
- Relevant source code for current implementation

### Step 3: Create Linear Ticket (reserves the ADR number)

**The Linear ticket number IS the ADR number.** No separate counter. Gaps in numbering are expected.

```
mcp__linear-server__save_issue:
  title: "ADR: {Decision Title}"
  team: "Hikmaai"
  project: "ADR Lifecycle"
  state: "In Progress"
  assignee: "me"
  priority: 2  (or as appropriate)
  description: "One-line summary.\n\nRepo: hikma-system-design\nBranch: adr/{NNN}-{kebab-title}"
```

Note the ticket identifier (e.g., `HIK-249`): the numeric part (249) is the ADR number.

### Step 4: Create Branch

```bash
cd ~/Development/hikmaAI/hikma-system-design
git checkout -b adr/{NNN}-{kebab-title} main
```

Example: `adr/249-mirsad-cryptographic-decision-trail`

### Step 5: Write the ADR

1. Copy `adr/TEMPLATE.md` to `adr/ADR-{NNN}-{kebab-title}.md`
2. Fill in all sections following the template guidance
3. Set frontmatter fields:
   - `**Status:** Drafting`
   - `**Linear:** [HIK-{NNN}](https://linear.app/hikmaai/issue/HIK-{NNN})`
   - `**Obsidian:** [[{NNN}-{kebab-title}]]`

Follow the HikmaAI ADR format exactly:

```markdown
# ADR-{NNN}: Title

- **Status:** Drafting
- **Date:** YYYY-MM-DD
- **Author:** Max Aroffo
- **Linear:** [HIK-{NNN}](https://linear.app/hikmaai/issue/HIK-{NNN})
- **Obsidian:** [[{NNN}-{kebab-title}]]
- **Context:** One-line summary of what prompted this
- **Tags:** #hikmaai #project #adr #topic1 #topic2
- **Second opinions:** (Optional. Summary of external review)

## Context

What converged to force this decision? Name specific inputs
(analysis, feedback, incidents, technical debt). 2-3 paragraphs max.

---

## Part A/B/C: [Themed Sections]

Break complex decisions into labeled parts. Each part:
- Current state (what exists)
- Analysis (options, trade-offs, comparisons)
- Tables for structured comparisons

Use as many parts as the decision requires. Simple ADRs may
have just Context + Decision + Consequences (no parts).

---

## Decision

State the decision clearly. Bold the core choice.
Rationale as bullet points. Include what was deferred and why.

## Technical Design (if applicable)

Concrete: API schemas, code snippets, config examples,
deployment patterns. Enough detail to implement from.

## Roadmap (if applicable)

Phased plan with dependencies. No time estimates in the ADR
itself (those go in implementation plans).

## Consequences

Bullet list: what follows from this decision.
Include both positive and negative consequences.

## Open Questions

Numbered list of unresolved items. Each should be a
specific question with concrete options, not vague.

## References

Links to external docs, internal vault notes, prior ADRs,
relevant source code.
```

### Step 6: Update README.md

Add a row to the ADR Index table in `hikma-system-design/README.md`:

```markdown
| {NNN} | {project} | {Title} | Drafting |
```

Also update the naming convention if it still references the old format.

### Step 7: Store in Vault

Save using the `obsidian` skill:

```bash
obsidian create name="Projects/HikmaAI/HLD/ADR-{NNN}-{Title}" content="..." silent
```

**Fallback** (direct file access):
Write to `/Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents/Projects/HikmaAI/HLD/ADR-{NNN}-{Title}.md`

### Step 8: Review

Run `dx-reviewer` agent on the ADR file, focusing on:

- Completeness (all sections present)
- Clarity (decisions unambiguous)
- Evidence (claims backed by data/code)
- Actionability (enough detail to implement)

Alternatively, if the ADR is short and straightforward, skip the agent and self-review against the checklist above.

### Step 9: Commit, Push, PR

**Commit:**
```bash
git add adr/ADR-{NNN}-{kebab-title}.md README.md [any other changed files]
git commit -m "docs: ADR-{NNN} {Title} (HIK-{NNN})

{One-line summary of the decision.}

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

**Push + PR:**
```bash
git push -u origin adr/{NNN}-{kebab-title}

gh pr create \
  --title "ADR-{NNN}: {Title}" \
  --body "## Summary
- **ADR-{NNN}**: {Decision summary}

**Linear:** [HIK-{NNN}](https://linear.app/hikmaai/issue/HIK-{NNN})

## Test plan
- [ ] Review ADR content for technical accuracy
- [ ] Verify README index entry

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

### Step 10: Update Linear Status

Move the ticket to "In Review" and attach the PR link:

```
mcp__linear-server__save_issue:
  id: "HIK-{NNN}"
  state: "In Review"
  links: [{"url": "{PR_URL}", "title": "PR: ADR-{NNN}"}]
```

### After Merge (manual or automated)

- Move Linear ticket to **Done**: `state: "Done"`
- Update ADR status to `**Status:** Accepted` (follow-up commit or part of next PR)
- GitHub Action syncs to Notion automatically

## ADR Status Lifecycle

| Status | Linear State | Meaning |
|--------|-------------|---------|
| **Proposed** | Todo | Number reserved, idea captured |
| **Drafting** | In Progress | ADR being written on feature branch |
| **In Review** | In Review | PR opened, team reviewing |
| **Accepted** | Done | PR merged, decision final |
| **Superseded** | Canceled | Replaced by a newer ADR (link to successor) |

## Numbering

| Rule | Detail |
|------|--------|
| **Source** | Linear ticket number (NNN from HIK-NNN) |
| **Legacy ADRs** | 001-032 keep their original numbers |
| **New ADRs** | Use the Linear ticket number (249, 250, ...) |
| **Gaps** | Expected and acceptable (rejected ADRs consume a number) |
| **Immutable** | Once assigned, the number never changes regardless of status |

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Filename | `ADR-NNN-kebab-title.md` | `ADR-249-mirsad-cryptographic-decision-trail.md` |
| Branch | `adr/NNN-kebab-title` | `adr/249-mirsad-cryptographic-decision-trail` |
| Linear ticket | `ADR: Title` | `ADR: Mirsad Cryptographic Decision Trail` |

## Style Rules

- No em dashes; use commas, colons, semicolons, or parentheses
- Tables for structured comparisons (always)
- Code blocks for API schemas, configs, deployment patterns
- Bold for core decisions and key terms
- `---` horizontal rules between major parts
- ASCII diagrams for architecture flows (no Mermaid in ADRs)

## Anti-patterns

| Bad | Good |
|-----|------|
| "We should probably..." | "Decision: X. Rationale: ..." |
| Options without trade-offs | Each option with pros/cons |
| Vague consequences | Specific, testable outcomes |
| Missing context | Name the trigger explicitly |
| Monolithic wall of text | Parts + tables + code blocks |
| Time estimates in ADR | Phases with dependencies only |
| Manual ADR numbering | Linear ticket = ADR number |
