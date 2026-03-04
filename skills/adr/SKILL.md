---
name: adr
description: "Write Architecture Decision Records following HikmaAI format. Use when user says write ADR, architecture decision, ADR, or decision record. Orchestrates refinement, research, writing, vault storage, and review. Not for implementation plans (use plan mode) or retrospectives (use learning-docs)."
---

# ABOUTME: Full ADR lifecycle: refine, research, write, store in vault, review
# ABOUTME: Follows HikmaAI format (Context, Parts, Decision, Technical Design, Roadmap, Consequences)

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

### Step 3: Write the ADR

Follow the HikmaAI ADR format exactly:

```markdown
# ADR-NNN: Title

- **Status:** Proposed | Accepted | Superseded by ADR-NNN
- **Date:** YYYY-MM-DD
- **Author:** Max Aroffo
- **Context:** One-line summary of what prompted this
- **Tags:** #hikmaai #project #adr #topic1 #topic2

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

### Step 4: Store in Vault

Save using the `obsidian` skill (CLI first, direct file Write as fallback):

```bash
# Determine next ADR number
obsidian search query="ADR-" path="Projects/HikmaAI/HLD" matches

# Create the ADR
obsidian create name="Projects/HikmaAI/HLD/ADR-NNN-Title" content="..." silent
```

**Fallback** (direct file access):
Write to `/Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents/Projects/HikmaAI/HLD/ADR-NNN-Title.md`

### Step 5: Review

Run `dx-reviewer` agent on the ADR file, focusing on:

- Completeness (all sections present)
- Clarity (decisions unambiguous)
- Evidence (claims backed by data/code)
- Actionability (enough detail to implement)

Alternatively, if the ADR is short and straightforward, skip the agent and self-review against the checklist above.

## Numbering

- Sequential: ADR-001, ADR-002, ADR-003...
- Check existing ADRs in `Projects/HikmaAI/HLD/` before assigning
- Never reuse a number, even if the ADR is superseded

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
