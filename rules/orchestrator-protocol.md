# ABOUTME: Autonomous development loop: implement, verify, review, fix, score
# ABOUTME: Routes software-engineer and review agents, enforces quality gates

# Orchestrator Protocol (Contractor Mode)

Enter after the goal is confirmed. REFINE and RESEARCH (steps 0 / 0b) run pre-plan; the main IMPLEMENT loop runs after plan approval. Exit at quality gate (score ≥ threshold), escalation (global round ceiling), plan checkpoint yield, or abandonment.

**Plan checkpoints** (`<!-- checkpoint:verify -->`, `<!-- checkpoint:decide -->`, see plan-first-workflow) halt the loop mid-IMPLEMENT: pause the current subtask, present state, resume only after human approval.

## SKIP_SET

Several steps skip for the same class of trivial tasks. "Skip for SKIP_SET" means:
- Typos, one-liners, single-function fixes with passing tests
- Config-only changes with no logic
- Pure documentation edits
- Any task with <10 changed lines and no new behavior

If the whole task is in SKIP_SET, skip the protocol entirely and edit directly.

## Loop

```
0.  REFINE       → see plan-first-workflow (gating rules live there)
0b. RESEARCH     → (optional) research-analyst for unknowns before planning
1.  IMPLEMENT    → software-engineer(s) with scoped subtasks (parallel if independent)
    1a. LOCALIZE → verify file list vs plan before editing
    1b. REPRODUCE → (bug-fix only) write script proving the bug exists
    1c. DRIFT    → verify alignment after each subtask
2.  VERIFY       → tests, lint, build, reproduction_confirmed
3.  REVIEW       → review agents by file pattern
4.  FIX          → software-engineer addresses CRITICAL/MAJOR findings
5.  RE-VERIFY    → rebuild, retest
5b. BLAST-RADIUS → (conditional) check related files for contradictions/staleness
6.  SCORE        → quality-gates thresholds
7.  LOOP         → repeat 3-7; global ceiling 5 rounds across REVIEW + UAT → escalate
8.  PRESENT      → summary: files changed, issues found/fixed, score, open items
9.  UAT          → goal-backward verification with human (skip for SKIP_SET)
10. STORE        → save session log + plan status (unconditional: also on escalation/abandonment, marking outcome)
```

## Research + Complexity (Step 0)

research-analyst searches docs/solutions/, LEARNING.md, MEMORY.md, vault, then external. Returns: comparison table, recommendation, ecosystem solutions (avoid hand-rolling), 1-2 common pitfalls. MUST end with complexity verdict:

| Level | Criteria | Effect |
|-------|----------|--------|
| simple | Known tech, <3 files, prior art exists | Standard flow |
| moderate | Some unknowns, 3-5 files | Standard flow |
| complex | Unfamiliar tech, >5 files, multiple approaches, no prior art, cross-cutting | Extended flow: write `quality_reports/research/YYYY-MM-DD_desc.md` + `/second-opinion` on approach + activate annotation cycle (see plan-first-workflow) |

## Implementation (Step 1)

Split into independent workstreams. Each software-engineer receives: **scope** (files), **plan** (subtask + criteria), **context** (lang/framework). Single-scope: implement directly. See parallelism rules below.

### Sub-protocols

| Sub-step | When it runs | How | Trace data | Skip when |
|----------|--------------|-----|------------|-----------|
| **LOCALIZE** (1a) | Before any edits | Engineer outputs `files_to_edit`. Orchestrator checks files exist and align with plan. WARN on extras. STOP on missing planned files UNLESS engineer provides `scope_reduction_rationale` (e.g., "File `X` turned out not to need editing because ..."). | `{files_planned, files_proposed, precision, recall, mismatches, scope_reduction_rationale?}` | Plan lists exact files; single-file task |
| **REPRODUCE** (1b) | Bug-fix only, after LOCALIZE | Script that FAILS on current code and PASSES after the fix. Target files from LOCALIZE. | `{script, fails_before_fix, passes_after_fix}` (passes_after_fix null until VERIFY) | Not a bug-fix; purely visual bug; plan says infeasible |
| **DRIFT** (1c) | After each subtask (including parallel ones, using `git diff -- <files_for_subtask>` to avoid races) | Fresh-context agent receives: subtask description + scoped diff. One question: "Did we build exactly this, no more, no less?" Verdict: aligned / minor drift (WARN, proceed) / significant drift (STOP). | `{subtask_id, verdict, deviations}` | Single subtask; trivial (<10 LOC) |

## VERIFY (Step 2)

Run tests, lint, build. Max 2 retries on flake; on the 3rd failure, STOP and escalate (same flow as Step 7 escalation).

If REPRODUCE ran (step 1b), also confirm `reproduction_confirmed = true`: the script that previously FAILED must now PASS. If not, the fix didn't address the reported bug; return to FIX.

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

## Blast Radius (Step 5b, conditional)

After RE-VERIFY, before SCORE. Detects entropy: docs, tests, imports still referencing pre-change behavior.

### Trigger (ANY of)

- Changed files add/remove/rename **exported symbols**. Detect with `ast-grep` or a **fully-qualified** regex (e.g., `\bMyModule\.MyFunc\b`). **Never naked grep** on common names like `get`, `init`, `render`: they explode to hundreds of false matches.
- More than 3 files changed
- Schema/migration changes, CLI flag definitions, REST/gRPC endpoint handlers

### How

1. **CLI pre-filter:** `ast-grep` or qualified regex for changed symbols; collect importers, docs, tests referencing them.
2. **Fresh-context agent** receives only snippets of related files (not full files). Flags stale references, old-behavior assertions, comments describing removed logic, broken imports.
3. **Report:** MAJOR (functional contradiction) or MINOR (stale comment/doc). CRITICAL contradictions re-enter FIX (step 4) before SCORE.

### Skip when

Docs-only; pure refactors with no API change; pre-filter found 0 related files.

## UAT: Goal-Backward Verification (Step 9)

UAT is **Outcome Verification with a human walkthrough**. The schema (observable truths → evidence → pass/fail) lives in `verification-protocol.md`; don't redefine it here.

Build the table from the goal (3-7 observable truths). Fill `Evidence` via CLI/output for every truth that can be verified mechanically. Use `AskUserQuestion` **only** for truths that need human judgment (visual, subjective, UX). On failure: feed into fix loop (step 4), re-verify, re-score, re-UAT failed items only. UAT→FIX rounds count against the global 5-round ceiling.

**Skip when:** in SKIP_SET.

## Rules

### Parallelism

| Agent class | Default | Max | Condition for max |
|-------------|---------|-----|-------------------|
| Read-only (research-analyst, review agents, explorers) | 5 | 7 | Always |
| Write (software-engineer) | 3 | 5 | File scopes disjoint AND no shared integration surfaces |

**Shared integration surfaces** (even a 1-line change needs a sequential wave): routing tables, barrel exports / `index.*`, DI container config, dependency manifests (`go.mod`, `package.json`), migrations directory, shared test fixtures.

If the plan requires edits to a shared surface, run the parallel batch first, then a **sequential INTEGRATE wave** for the shared files.

### Permissions

- Review agents: read-only.
- software-engineer: read-write, scoped to assigned files.

### Escalation (Step 7, global ceiling)

`total_fix_rounds` counts every REVIEW→FIX cycle AND every UAT→FIX cycle. When it reaches 5 without meeting the score threshold, STOP and escalate.

Present to the human:
- Current score and threshold
- Top 3 unresolved findings (CRITICAL/MAJOR)
- Round-by-round score delta
- Hypothesis on why progress stalled
- Options: lower threshold, accept remaining risk, re-plan, abandon

### Just-do-it mode

Skip final approval and auto-commit when ALL of: SCORE ≥ 80, no CRITICAL findings, BLAST-RADIUS clean. **Bypasses UAT** (no human walkthrough possible in this mode). Stops at a local commit on the feature branch: does not push, does not open a PR.

## Trace Capture

Use the `harness-trace` skill (schema, JSONL format, capture logic).

Trace is skipped for SKIP_SET. Trace files are local-only (gitignored).
