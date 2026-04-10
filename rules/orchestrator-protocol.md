# ABOUTME: Autonomous development loop — implement, verify, review, fix, score
# ABOUTME: Routes software-engineer and review agents, enforces quality gates

# Orchestrator Protocol (Contractor Mode)

After plan approval, execute autonomously until quality gates pass.

## Loop

```
0.  REFINE       → requirements refinement (see plan-first-workflow) if request is ambiguous
0b. RESEARCH     → (optional) research-analyst for unknowns before planning
1.  IMPLEMENT    → software-engineer(s) with scoped subtasks (parallel if independent)
    1a. LOCALIZE → (within IMPLEMENT) verify file list vs plan before editing
    1b. REPRODUCE → (bug-fix only, after LOCALIZE) write script proving the bug exists
    1c. DRIFT    → (multi-subtask) verify alignment after each subtask before next
2.  VERIFY       → tests, lint, build (max 2 retries)
3.  REVIEW       → review agents by file pattern
4.  FIX          → software-engineer addresses CRITICAL/MAJOR findings (requirements, not suggestions)
5.  RE-VERIFY    → rebuild, retest
5b. BLAST-RADIUS → (conditional) check related files for contradictions/staleness
6.  SCORE        → quality-gates thresholds
7.  LOOP         → repeat 3-7 until score ≥ threshold or max 5 rounds
8.  PRESENT      → summary: files changed, issues found/fixed, score, open items
9.  UAT          → goal-backward verification with human (skip for docs-only, config, refactors)
10. STORE        → save session log + plan status to vault (see plan-first-workflow)
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

**Checkpoints:** see plan-first-workflow. Engineers apply deviation rules (R1-R6) for unplanned discoveries.

### Localization Sub-Protocol (Step 1a)

Before editing any files, the software-engineer outputs the list of files to modify. The orchestrator compares this against the plan's file scope (arxiv 2604.05013: atomic skill "localization").

**How:** engineer includes a `files_to_edit` list at the start of implementation. Orchestrator checks:
- All proposed files exist in the repo
- Proposed files align with the plan scope (precision: correct/proposed, recall: correct/planned)
- Mismatches flagged as WARN (extra files) or STOP (missing planned files)

**Trace:** `LOCALIZE` with `{files_planned, files_proposed, precision, recall, mismatches}`. The `localization_precision` is also recorded in `IMPLEMENT` data for correlation.

**Skip when:** plan lists exact files (no ambiguity), single-file task, or trivial change (<10 lines).

### Issue Reproduction (Step 1b, bug-fix only)

After localization, prove the bug exists with a reproduction script (arxiv 2604.05013: atomic skill "reproduction"). Runs after LOCALIZE so the agent knows which files/entry points to target.

**How:** write a script/test that triggers the reported failure on the current codebase. Two conditions for success:
1. Script **fails** on the broken code (verified now)
2. Script **passes** after the fix (verified during VERIFY, step 2)

**Trace:** `REPRODUCE` with `{script, fails_before_fix, passes_after_fix}`. `passes_after_fix` is null until VERIFY completes.

**Skip when:** not a bug-fix task, bug is purely visual (no scriptable assertion), or the plan explicitly states reproduction is not feasible.

### Mid-Implementation Drift Check (Step 1c, multi-subtask only)

When implementation has 2+ sequential subtasks, verify alignment after each subtask before launching the next. This prevents cascading deviations where subtask N+1 builds on a drifted subtask N.

**How:** spawn a lightweight, isolated agent (fresh context) that receives ONLY:
1. The subtask description from the plan (what was supposed to happen)
2. The `git diff` of changes made during the subtask

**The agent answers one question:** "Did we build exactly this, no more, no less?"

| Verdict | Action |
|---------|--------|
| Aligned | Proceed to next subtask |
| Minor drift (extra work, style) | Log as WARN, proceed |
| Significant drift (wrong approach, missing requirements, scope creep) | STOP. Correct before next subtask |

**Skip when:** single subtask, subtask is trivial (<10 lines changed), or subtasks are fully parallel (no sequential dependency).

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

## Blast Radius Check (Step 5b, conditional)

After RE-VERIFY, before SCORE. Detects entropy: documentation, tests, and imports that still reference pre-change behavior.

### Trigger conditions (ANY of)

- Changed files modify public APIs (exported functions, class interfaces, REST endpoints, CLI flags)
- More than 3 files changed
- Schema/migration changes

**Skip when:** no trigger condition met, docs-only changes, pure refactors with no API change.

### How it works

1. **CLI pre-filter (cheap):** `grep`/`rg` for references to changed function names, class names, endpoints across the repo. Collect the set of "related files" (importers, docs, tests referencing changed symbols).
2. **Fresh-context agent:** receives ONLY the list of changed files, what changed (summary), and the related files found by grep. Checks each related file for:
   - Stale references to old behavior (doc says X, code now does Y)
   - Tests asserting old behavior
   - Comments describing removed/changed logic
   - Import paths that no longer exist
3. **Report:** each finding as MAJOR (functional contradiction) or MINOR (stale comment/doc). Findings feed into SCORE.

### Cost control

- The grep pre-filter keeps agent input small: only files that actually reference changed symbols
- Agent receives file snippets (relevant lines), not full files
- If grep finds 0 related files outside the changed set, skip the agent entirely

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
| LOCALIZE | files_planned, files_proposed, files_actually_changed, precision, recall, mismatches |
| REPRODUCE | script, fails_before_fix, passes_after_fix (null until VERIFY) |
| IMPLEMENT | agents launched, files_changed, subtask_count, localization_precision |
| DRIFT_CHECK | subtask_id, verdict (aligned/minor_drift/significant_drift), deviations [{desc}] |
| VERIFY | tests_pass, lint_clean, build_ok, retries, reproduction_confirmed |
| REVIEW | agents activated, findings {CRITICAL/MAJOR/MINOR: count}, review_validity |
| FIX | findings_addressed, deviations [{rule, desc}] |
| BLAST_RADIUS | triggered, trigger_reason, files_scanned, contradictions {MAJOR: count, MINOR: count} |
| SCORE | score, threshold, gate |
| LOOP | round, total_rounds, exit_reason |
| UAT | performed, items, passed, failed |
| SUMMARY | tokens_in, tokens_out, model, duration_min, files_changed, final_score |

Format: `{"v":1,"session":"<slug>","ts":"<ISO>","step":"<STEP>","data":{...}}`

Skip for: docs-only, config, single-function fixes. Trace files are local-only (gitignored).
