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
9. UAT       → goal-backward verification with human (skip for docs-only, config, refactors)
10. STORE    → save session log + plan status to vault (see plan-first-workflow)
```

## Research + Complexity (Step 0)

research-analyst searches docs/solutions/, LEARNING.md, MEMORY.md, vault, then external. Returns: comparison table, recommendation, ecosystem solutions (avoid hand-rolling), 1-2 common pitfalls. MUST end with complexity verdict:

| Level | Criteria | Effect |
|-------|----------|--------|
| simple | Known tech, <3 files, prior art exists | Standard flow |
| moderate | Some unknowns, 3-5 files | Standard flow |
| complex | Unfamiliar tech, >5 files, multiple approaches, no prior art, cross-cutting | Extended flow: write `quality_reports/research/YYYY-MM-DD_desc.md` + `/second-opinion` on approach + activate annotation cycle (see plan-first-workflow) |

## Implementation (Step 1)

Split into independent workstreams. Each software-engineer gets: **scope** (files), **plan** (subtask + criteria), **context** (lang/framework). Max 3 parallel. Single-scope → implement directly.

**Checkpoints:** see plan-first-workflow. Engineers apply deviation rules (R1-R4) for unplanned discoveries.

## Review Routing (Step 3)

| Pattern | Agents |
|---------|--------|
| `*.go`, `*.rb`, `*.py`, `*.ts`, `*.kt`, `*.swift` | architecture + security |
| Hot paths, queries, caching | + performance |
| `*_test.*`, `*_spec.*` | + test + test-design-reviewer |
| `go.mod`, `Gemfile`, `package.json`, `pyproject.toml` | dependency |
| `migrations/`, `schema.rb`, `*.sql` | database |
| `docs/`, `README*`, `ADR/`, `*.md` | dx |
| No match | architecture + security (minimum) |

## UAT: Goal-Backward Verification (Step 9)

Verify the work achieves the user's goal, not just that code passes tests.

1. **Derive must-be-true list** from the goal (3-7 observable behaviors, not implementation details)
2. **Walkthrough** each via `AskUserQuestion`: Pass / Fail / Skip
3. **On failure:** feed into fix loop (step 4), re-verify, re-score, re-UAT failed items only

**Skip when:** docs-only, config, pure refactors, single-function fixes with passing tests.

## Rules

- Max 3 agents parallel
- Review agents: read-only. software-engineer: read-write, scoped.
- "Just do it" mode: skip final approval, auto-commit if score ≥ 80. Full review loop still runs.

## Trace Capture

After each orchestrator step, append a JSONL line to `quality_reports/traces/YYYY-MM-DD_<session-slug>.jsonl`:

| Step | Data to capture |
|------|-----------------|
| REFINE | ambiguities_found, questions_asked |
| RESEARCH | complexity, sources_consulted |
| IMPLEMENT | agents launched, files_changed, subtask_count |
| VERIFY | tests_pass, lint_clean, build_ok, retries |
| REVIEW | agents activated, findings {CRITICAL/MAJOR/MINOR: count} |
| FIX | findings_addressed, deviations [{rule, desc}] |
| SCORE | score, threshold, gate |
| LOOP | round, total_rounds, exit_reason |
| UAT | performed, items, passed, failed |
| SUMMARY | tokens_in, tokens_out, model, duration_min, files_changed, final_score |

Format: `{"v":1,"session":"<slug>","ts":"<ISO>","step":"<STEP>","data":{...}}`

Skip for: docs-only, config, single-function fixes. Trace files are local-only (gitignored).
