# ABOUTME: Spine of the autonomous development loop: steps, SKIP_SET, literal report lines, invariants
# ABOUTME: The full protocol lives in the `orchestrator` skill, loaded on demand at the first step run

# Orchestrator Protocol (Contractor Mode)

The autonomous loop: implement, verify, review, fix, score. Enter after the goal is confirmed. Exit at the quality gate, at escalation, at a plan checkpoint, or on abandonment.

**Load the `orchestrator` skill at the first step you actually run**, which is step 0 whenever research or refinement happens, not step 1: it owns the complexity verdict step 0 produces and the `/goal` proposal made at plan approval, both of which fire before implementation. It carries the rest of the detail too: sub-protocols, review routing, blast radius, UAT, parallelism, effort, escalation, goal-backed runs. This file is only the spine.

## SKIP_SET

Typos, one-liners, single-function fixes with passing tests; config-only changes with no logic; pure documentation edits; anything under 10 changed lines with no new behavior. A task entirely in SKIP_SET skips the protocol: edit directly, no skill load, no trace.

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
4.  FIX          → software-engineer addresses Critical/Major findings
5.  RE-VERIFY    → rebuild, retest
5b. BLAST-RADIUS → (conditional) check related files for contradictions/staleness
6.  SCORE        → quality-gates thresholds
7.  LOOP         → repeat 3-7 until the plan's fix-round budget is spent (default 5 when no plan declares one) → escalate
8.  PRESENT      → summary: files changed, issues found/fixed, score, open items
9.  UAT          → goal-backward verification with human (skip for SKIP_SET)
10. STORE        → save session log + close the plan: fill Outcomes & Retrospective, move active/ → completed/ (unconditional: also on escalation/abandonment, marking outcome)
```

## Literal report lines

The trace extractor keys on these exact forms. Free-form phrasing ("quality looks good") is invisible in telemetry: it produced 0 SCORE events across 6 traced sessions.

```
LOCALIZE: planned=<n> proposed=<m> precision=<p> recall=<r> mismatches=none|<file1,file2>
REPRODUCE: script=<path> fails_before_fix=true|false
DRIFT: subtask=<id> verdict=aligned|minor_drift|significant_drift
EXECUTOR: pi-exec model=<id> subtask=<id>
BLAST-RADIUS: clean (files_checked=<k>) | MAJOR=<n> MINOR=<m> (files_checked=<k>) | skipped (<reason>)
SCORE: <n>/100 (threshold: <t>, gate: commit|pr|excellence)
```

A SCORE is a judge verdict, valid only alongside fresh computational evidence: a successful test/lint/build run after the last source edit (`score-evidence-guard` enforces this). If VERIFY ran inside a subagent, say so when reporting.

## Invariants

- Review agents are read-only. software-engineer is read-write, scoped to its assigned files.
- The orchestrator is the sole committer. pi never commits, never takes a review or spec role (rules, agents and skills are spec), and every pi-executed subtask gets a DRIFT check.
- Fix-round ceiling, writer concurrency and finalization evidence come from the plan's Budget (plan-first-workflow). Hitting a limit means escalate; it never means stop quietly with a fluent summary.
