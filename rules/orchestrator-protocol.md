# ABOUTME: Autonomous development loop — implement, verify, review, fix, score
# ABOUTME: Routes software-engineer and review agents, enforces quality gates

# Orchestrator Protocol (Contractor Mode)

After plan approval, execute autonomously until quality gates pass.

## Loop

```
1. IMPLEMENT → Launch software-engineer agent(s) with scoped subtasks
2. VERIFY    → Run tests, lint, build (max 2 retries on failure)
3. REVIEW    → Launch review agents by file pattern (see routing below)
4. FIX       → Pass reviewer findings to software-engineer — findings are requirements
5. RE-VERIFY → Rebuild, retest
6. SCORE     → Apply quality-gates thresholds
7. LOOP      → Repeat 3-7 until score ≥ threshold or max 5 rounds
8. PRESENT   → Structured summary: files changed, issues found/fixed, score, open items
```

## Implementation (Step 1)

Split the plan into **independent workstreams**. Launch `software-engineer` agents in parallel for each.

Each agent receives:
- **Scope:** files/directories it owns (no cross-boundary edits)
- **Plan:** specific subtask with acceptance criteria
- **Context:** relevant language/framework skill

```
# Example: full-stack feature
Plan has 3 independent subtasks:
1. software-engineer: "Add /api/orders endpoint" → scope: internal/ordering/
2. software-engineer: "Add OrderList component"  → scope: src/components/orders/
3. software-engineer: "Add orders migration"     → scope: db/migrations/
→ Launch all 3 in parallel, wait for all, then verify
```

For single-scope tasks, implement directly without launching a subagent.

## Fix Round (Step 4)

Pass reviewer findings back to `software-engineer` with:
- The exact findings (severity + location + proposed fix)
- Clear instruction: **CRITICAL and MAJOR are requirements, not suggestions**
- The agent must explain any deviation from proposed fixes

## Review Agent Routing (Step 3)

Launch review agents **in parallel** based on changed files. Only launch what's relevant.

| File pattern | Agents |
|-------------|--------|
| `*.go`, `*.rb`, `*.py`, `*.ts`, `*.kt`, `*.swift` | architecture-reviewer + security-reviewer |
| Hot paths, queries, loops, caching | + performance-reviewer |
| `*_test.go`, `*_spec.rb`, `*_test.py`, `*.test.ts` | + test-reviewer |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency-reviewer |
| `migrations/`, `schema.rb`, `*.sql` | database-reviewer |
| `docs/`, `README*`, `ADR/`, `*.md` (non-code) | dx-reviewer |
| No specific match | architecture-reviewer + security-reviewer (minimum) |

## Parallel Rules

- Max 3 agents in parallel per round (implementation or review)
- Review agents are **read-only** — report findings, never edit files
- `software-engineer` is **read-write** — scoped to assigned files only
- Each review agent produces severity-ranked findings: CRITICAL / MAJOR / MINOR

## "Just Do It" Mode

When user says "just do it" or similar:
- Skip final approval pause
- Auto-commit if score ≥ 80
- Still run full review loop — no shortcuts on quality
