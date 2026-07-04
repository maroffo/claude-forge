# ABOUTME: HikmaAI ADR document format, section-by-section, used verbatim when writing an ADR
# ABOUTME: Reference for the adr skill Step 5 (Write the ADR); do not restructure the process here

# HikmaAI ADR Format

Follow this format exactly when filling in `adr/ADR-{NNN}-{kebab-title}.md`.

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
