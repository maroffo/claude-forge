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

## Session Analysis

Analyze past sessions to identify improvement opportunities. Session files live in `~/.claude/projects/` (project paths: slashes→dashes).

### CRITICAL Rules

- **NEVER read raw session files** (100k+ lines, token killer)
- **ALWAYS use jq** to extract summaries
- Focus on patterns, not individual messages

### What to Look For

| Pattern | Example | Fix |
|---------|---------|-----|
| Token waste | Read same file 5+ times | Cache key info, update CLAUDE.md |
| Wrong paths | Built feature, then found existing code | Better initial search, architecture docs |
| Repeated mistakes | Same lint error 3 sessions | Pre-commit hook, CLAUDE.md note |
| Missing automation | Manual steps every session | Script it, add to workflow |
| Context loss | Re-learn after compaction | Save state to LEARNING.md before limit |

### Analysis Commands

```bash
# List project sessions
ls ~/.claude/projects/

# Count tool calls by type (find most used)
jq '[.messages[].content[]? | select(.type=="tool_use") | .name] | group_by(.) | map({tool: .[0], count: length}) | sort_by(-.count)' \
  ~/.claude/projects/PROJECT_NAME/session_*.json

# Find repeated file reads (>3 times)
jq -r '.messages[].content[]? | select(.type=="tool_use" and .name=="Read") | .input.file_path' \
  ~/.claude/projects/PROJECT_NAME/session_*.json | sort | uniq -c | sort -rn | head -20

# Extract error patterns
jq -r '.messages[].content[]? | select(.type=="tool_result" and (.content | tostring | test("error|Error|ERROR"))) | .content' \
  ~/.claude/projects/PROJECT_NAME/session_*.json | head -50

# Summarize session themes (tool uses + key phrases)
jq -r '.messages[] | select(.role=="assistant") | .content[]? | select(.type=="text") | .text' \
  ~/.claude/projects/PROJECT_NAME/session_*.json | grep -E "^(Let me|I'll|Looking at|The issue)" | head -30
```

### Propose Improvements As

1. **CLAUDE.md updates** - Workflow rules, decision frameworks
2. **New skills** - Repeated patterns → automation
3. **Scripts** - Multi-step commands done often
4. **LEARNING.md entries** - Project-specific gotchas
5. **Pre-commit hooks** - Catch issues earlier

### Example Analysis

```bash
# Session shows Read tool called 15 times on same config file
# → Add key config values to CLAUDE.md project file
# → Create "config summary" script

# Multiple sessions fixing same linting error
# → Add to CLAUDE.md "Common Issues" section
# → Strengthen pre-commit hook

# Context loss after compaction, re-learned architecture
# → Update LEARNING.md Architecture section
# → Add mermaid diagram for quick re-orientation
```
