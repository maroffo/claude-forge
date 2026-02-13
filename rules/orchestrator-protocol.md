# ABOUTME: Autonomous development loop — implement, verify, review, fix, score
# ABOUTME: Routes software-engineer and review agents, enforces quality gates

# Orchestrator Protocol (Contractor Mode)

After plan approval, execute autonomously until quality gates pass.

## Loop

```
0. REFINE    → requirements refinement (see plan-first-workflow) if request is ambiguous
0b. RESEARCH → (optional) research-analyst for unknowns before planning
1. IMPLEMENT → software-engineer(s) with scoped subtasks (parallel if independent)
2. VERIFY    → tests, lint, build (max 2 retries)
3. REVIEW    → review agents by file pattern
4. FIX       → software-engineer addresses CRITICAL/MAJOR findings (requirements, not suggestions)
5. RE-VERIFY → rebuild, retest
6. SCORE     → quality-gates thresholds
7. LOOP      → repeat 3-7 until score ≥ threshold or max 5 rounds
8. PRESENT   → summary: files changed, issues found/fixed, score, open items
```

## Research + Complexity (Step 0)

research-analyst searches `docs/solutions/`, `LEARNING.md`, `MEMORY.md`, then external. Returns comparison table + recommendation. MUST end with complexity verdict:

| Level | Criteria | Effect |
|-------|----------|--------|
| simple | Known tech, <3 files, prior art exists | Standard flow |
| moderate | Some unknowns, 3-5 files | Standard flow |
| complex | Unfamiliar tech, >5 files, multiple approaches, no prior art, cross-cutting | Extended flow: write `quality_reports/research/YYYY-MM-DD_desc.md` + activate annotation cycle (see plan-first-workflow) |

## Implementation (Step 1)

Split into independent workstreams. Each software-engineer gets: **scope** (files), **plan** (subtask + criteria), **context** (lang/framework). Max 3 parallel. Single-scope → implement directly.

**Checkpoints:** If plan contains `<!-- checkpoint:verify -->` or `<!-- checkpoint:decide -->` markers, software-engineer stops at those points for human input. Between checkpoints, execution is autonomous. Engineers apply deviation rules (R1-R4) for unplanned discoveries.

## Review Routing (Step 3)

| Pattern | Agents |
|---------|--------|
| `*.go`, `*.rb`, `*.py`, `*.ts`, `*.kt`, `*.swift` | architecture + security |
| Hot paths, queries, caching | + performance |
| `*_test.*`, `*_spec.*` | + test |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency |
| `migrations/`, `schema.rb`, `*.sql` | database |
| `docs/`, `README*`, `ADR/`, `*.md` | dx |
| No match | architecture + security (minimum) |

## Rules

- Max 3 agents parallel
- Review agents: read-only. software-engineer: read-write, scoped.
- "Just do it" mode: skip final approval, auto-commit if score ≥ 80. Full review loop still runs.
