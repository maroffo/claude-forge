# ABOUTME: Autonomous development loop — implement, verify, review, fix, score
# ABOUTME: Routes software-engineer and review agents, enforces quality gates

# Orchestrator Protocol (Contractor Mode)

After plan approval, execute autonomously until quality gates pass.

## Loop

```
0. RESEARCH  → (optional) Launch research-analyst for unknowns before planning
1. IMPLEMENT → Launch software-engineer(s) with scoped subtasks (parallel if independent)
2. VERIFY    → Run tests, lint, build (max 2 retries)
3. REVIEW    → Launch review agents by file pattern
4. FIX       → Pass findings to software-engineer — CRITICAL/MAJOR are requirements
5. RE-VERIFY → Rebuild, retest
6. SCORE     → Apply quality-gates thresholds
7. LOOP      → Repeat 3-7 until score ≥ threshold or max 5 rounds
8. PRESENT   → Summary: files changed, issues found/fixed, score, open items
```

## Research (Step 0)

Launch `research-analyst` when the plan involves unfamiliar tech, multiple valid approaches, or no internal prior art. The agent searches `docs/solutions/`, `LEARNING.md`, `MEMORY.md`, then external sources. Returns a comparison table + recommendation. Skip for well-understood tasks.

## Implementation (Step 1)

Split plan into independent workstreams. Each `software-engineer` gets: **scope** (files it owns), **plan** (subtask + acceptance criteria), **context** (language/framework). Max 3 parallel. Single-scope tasks → implement directly.

## Review Agent Routing (Step 3)

| File pattern | Agents |
|-------------|--------|
| `*.go`, `*.rb`, `*.py`, `*.ts`, `*.kt`, `*.swift` | architecture-reviewer + security-reviewer |
| Hot paths, queries, caching | + performance-reviewer |
| `*_test.go`, `*_spec.rb`, `*_test.py`, `*.test.ts` | + test-reviewer |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency-reviewer |
| `migrations/`, `schema.rb`, `*.sql` | database-reviewer |
| `docs/`, `README*`, `ADR/`, `*.md` (non-code) | dx-reviewer |
| No specific match | architecture-reviewer + security-reviewer (minimum) |

## Rules

- Max 3 agents in parallel (implementation or review)
- Review agents: **read-only**. `software-engineer`: **read-write**, scoped.
- "Just do it" mode: skip final approval, auto-commit if score ≥ 80. Full review loop still runs.
