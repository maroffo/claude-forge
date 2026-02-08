# ABOUTME: Autonomous development loop — implement, verify, review, fix, score
# ABOUTME: Routes review agents by file pattern, enforces quality gates before completion

# Orchestrator Protocol (Contractor Mode)

After plan approval, execute autonomously until quality gates pass.

## Loop

```
1. IMPLEMENT → Execute plan steps
2. VERIFY    → Run tests, lint, build (max 2 retries on failure)
3. REVIEW    → Launch agents by file pattern (see routing below)
4. FIX       → Apply findings: Critical → Major → Minor
5. RE-VERIFY → Rebuild, retest
6. SCORE     → Apply quality-gates thresholds
7. LOOP      → Repeat 3-7 until score ≥ threshold or max 5 rounds
8. PRESENT   → Structured summary: files changed, issues found/fixed, score, open items
```

## Agent Routing

Launch agents **in parallel** based on changed files. Only launch what's relevant.

| File pattern | Agents |
|-------------|--------|
| `*.go`, `*.rb`, `*.py`, `*.ts`, `*.kt`, `*.swift` | architecture-reviewer + security-reviewer |
| Hot paths, queries, loops, caching | + performance-reviewer |
| `*_test.go`, `*_spec.rb`, `*_test.py`, `*.test.ts` | + test-reviewer |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency-reviewer |
| `migrations/`, `schema.rb`, `*.sql` | database-reviewer |
| `docs/`, `README*`, `ADR/`, `*.md` (non-code) | dx-reviewer |
| No specific match | architecture-reviewer + security-reviewer (minimum) |

## Parallel Agent Rules

- Max 3 agents in parallel per round
- All review agents are **read-only** — report findings, never edit files
- Orchestrator (you) applies fixes based on agent reports
- Each agent produces severity-ranked findings: CRITICAL / MAJOR / MINOR

## "Just Do It" Mode

When user says "just do it" or similar:
- Skip final approval pause
- Auto-commit if score ≥ 80
- Still run full review loop — no shortcuts on quality
