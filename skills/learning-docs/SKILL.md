---
name: learning-docs
description: "Create and update LEARNING.md project retrospectives. Use to document architecture decisions, lessons learned, bugs fixed, and technical insights."
---

# ABOUTME: Project knowledge capture through engaging LEARNING.md files
# ABOUTME: Documents architecture, decisions, bugs, lessons learned in conversational style

# Learning Documentation

## Purpose

Capture project knowledge in `LEARNING.md` - a living document that grows with the project. Not boring docs, but engaging technical storytelling.

## When to Update

- After fixing non-trivial bugs
- After architectural decisions
- After integrating new tech
- After solving tricky problems
- Before context switches (end of day/week)

## Structure

```markdown
# LEARNING.md

## Project Overview
What this project does, why it exists, who it's for.

## Architecture
How the pieces fit together. Use diagrams (mermaid) where helpful.
Explain the "why" behind structural decisions.

## Tech Stack & Decisions
| Technology | Why We Chose It | Trade-offs |
|------------|-----------------|------------|

## Lessons Learned

### [Date] Title of Lesson
**Context:** What we were trying to do
**Problem:** What went wrong or was tricky
**Solution:** How we fixed it
**Takeaway:** What to remember for next time

## Pitfalls & Gotchas
Things that bit us. Save future-you from repeating mistakes.

## Best Practices Discovered
Patterns that worked well in this codebase.
```

## Writing Style

| Do | Don't |
|----|-------|
| Conversational tone | Dry technical prose |
| Analogies that clarify | Jargon without context |
| Concrete examples | Abstract descriptions |
| "We tried X, it broke because Y" | "X is not recommended" |
| Honest about mistakes | Sanitized corporate-speak |

## Examples

**Good:**
> We spent 2 hours debugging why webhooks weren't firing. Turns out Redis was silently dropping messages when memory hit 80%. Added `maxmemory-policy volatile-lru` and monitoring. Lesson: always monitor your message queues, silence is not golden.

**Bad:**
> Webhook reliability was improved by adjusting Redis configuration parameters.

## Commands

```bash
# Check if LEARNING.md exists
ls -la LEARNING.md

# Show recent git activity for context
git log --oneline -10
git diff --stat HEAD~5
```

## Workflow

1. **Read** existing LEARNING.md (or create if missing)
2. **Review** recent work (git log, changed files)
3. **Ask** what was learned, what was tricky, what decisions were made
4. **Append** new lessons in conversational style
5. **Keep** entries dated and searchable
