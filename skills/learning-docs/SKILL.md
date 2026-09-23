---
name: learning-docs
description: "Create and update LEARNING.md project retrospectives. Use when user says retrospective, lessons learned, what did we learn, document decisions, or session analysis."
---

# ABOUTME: Project knowledge capture through engaging LEARNING.md files
# ABOUTME: Documents architecture, decisions, bugs, lessons learned in conversational style

# Learning Documentation

## Quality Notes

- Quality of insights matters more than covering every change
- Re-read what you wrote: is it useful to a future reader, or just filler?

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

Illustrative only: every fact in a lesson (durations, numbers, causes, fixes) comes from the session, the git history, or the user. When a detail is unknown, leave it out or ask; never invent one to make the story vivid.

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
6. **Mirror lessons to vault** (below): cross-project archive, blog discovery, knowledge-sync input

**Vault copy (lessons):** after appending to LEARNING.md, also append each new lesson to the vault (create the note first with `obsidian create name="<project> - Learnings" silent` if missing; command syntax in `_OBSIDIAN.md`):

```bash
obsidian append file="<project> - Learnings" content="### YYYY-MM-DD: <title>\n<Context → Problem → Solution → Takeaway, condensed to a few lines>"
```

The repo's LEARNING.md stays the source of truth. If the obsidian CLI is unavailable, skip (do not use the path fallback; the repo copy is authoritative).

**Vault privacy (applies to EVERY vault copy in this skill: lessons, solutions, skill candidates):** for work projects (HikmaAI, client repos), mirror only content safe outside the work perimeter. Exclude client names, internal hostnames and architecture details, unreleased product information, anything under NDA. When in doubt, keep it repo-only.

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
[Root cause or design rationale, 1-3 sentences]
```

**When to use LEARNING.md vs solutions/**: LEARNING.md for narrative retrospectives, architectural decisions, broad lessons. Solutions/ for specific, searchable, reusable fixes; "how did we solve X?" answers.

**Vault copy:** After writing to `docs/solutions/`, also append to vault: `obsidian append file="<project> - Solutions" content="### YYYY-MM-DD: [title]\n[Problem/Solution/Why]"`. Creates cross-project discoverability.

## Session Analysis

Analyze past sessions to identify improvement opportunities. Session files live in `~/.claude/projects/` (project paths: slashes→dashes).

### Extraction

Session files run to 100k+ lines, so extract summaries with jq instead of reading them raw, and look for patterns rather than individual messages.

### What to Look For

| Pattern | Example | Fix |
|---------|---------|-----|
| Token waste | Read same file 5+ times | Cache key info, update CLAUDE.md |
| Wrong paths | Built feature, then found existing code | Better initial search, architecture docs |
| Repeated mistakes | Same lint error 3 sessions | Pre-commit hook, CLAUDE.md note |
| Missing automation | Manual steps every session | Script it, add to workflow |
| Context loss | Re-learn after compaction | Save state to LEARNING.md before limit |

### Key jq Commands

Sessions live in `~/.claude/projects/PROJECT_NAME/<session-id>.jsonl`, one event per line; message content sits under `.message.content`.

- **Tool call counts:** `jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .name' SESSION.jsonl | sort | uniq -c | sort -rn`
- **Repeated reads:** `jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Read") | .input.file_path' SESSION.jsonl | sort | uniq -c | sort -rn | head -20`
- **Error patterns:** `jq -r 'select(.type=="user") | .message.content | arrays | .[] | select(.type=="tool_result" and .is_error==true) | .content | tostring' SESSION.jsonl | head -50`

### Propose Improvements As

CLAUDE.md updates, new skills, scripts, LEARNING.md entries, pre-commit hooks.

### Vault Pattern Annotation

When a lesson learned maps to a skill domain, append to `## Skill Candidates` in the relevant Second Brain note:

```bash
obsidian append file="Second Brain - Development" content="\n| <pattern> | <target-skill> | <project> | YYYY-MM-DD | weak |"
```

Signal starts as `weak`. The `knowledge-sync` skill promotes to `strong` when 3+ projects or 2+ independent sources confirm the pattern. Create the `## Skill Candidates` section (with table header) if it doesn't exist yet.

