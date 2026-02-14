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

Sections: **Project Overview**, **Architecture** (mermaid diagrams), **Tech Stack & Decisions** (table: Technology | Why | Trade-offs), **Lessons Learned** (dated: Context → Problem → Solution → Takeaway), **Pitfalls & Gotchas**, **Best Practices Discovered**

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

## Workflow

1. **Read** existing LEARNING.md (or create if missing)
2. **Review** recent work (`git log --oneline -10`)
3. **Ask** what was learned, what was tricky
4. **Append** new lessons in conversational style (dated, searchable)
5. **Capture solutions** in `docs/solutions/[category]/` for searchable reuse

## Solutions Directory

For solved problems worth referencing again, create files in `docs/solutions/`:

```
docs/solutions/
├── auth/           → Authentication, authorization, sessions
├── performance/    → Profiling, caching, optimization
├── infrastructure/ → CI/CD, Docker, deployment
├── database/       → Migrations, queries, indexing
├── testing/        → Patterns, fixtures, flaky test fixes
└── debugging/      → Hard bugs, investigation techniques
```

**Format:** `docs/solutions/[category]/YYYY-MM-DD_short-description.md`

Each solution file:
```markdown
# Problem
[What broke / what we needed]

# Solution
[What fixed it, with code if relevant]

# Why It Works
[Root cause or design rationale — 1-3 sentences]
```

**When to use LEARNING.md vs solutions/**: LEARNING.md for narrative retrospectives, architectural decisions, broad lessons. Solutions/ for specific, searchable, reusable fixes — "how did we solve X?" answers.

**Vault copy:** After writing to `docs/solutions/`, also append to vault: `obsidian append file="<project> - Solutions" content="### YYYY-MM-DD: [title]\n[Problem/Solution/Why]"`. Creates cross-project discoverability.

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

### Vault Pattern Annotation

When a lesson learned maps to a skill domain, append to `## Skill Candidates` in the relevant Second Brain note:

```bash
obsidian append file="Second Brain - Development" content="\n| <pattern> | <target-skill> | <project> | YYYY-MM-DD | weak |"
```

Signal starts as `weak`. The `knowledge-sync` skill promotes to `strong` when 3+ projects or 2+ independent sources confirm the pattern. Create the `## Skill Candidates` section (with table header) if it doesn't exist yet.

