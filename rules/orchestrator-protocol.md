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
3.  REVIEW       → review agents by file pattern, launched in BACKGROUND + worktree-isolated (they never block, never touch the main tree); findings reach FIX consolidated, then persisted per round (see orchestrator skill, Finding Consolidation + Review Artifacts)
4.  FIX          → software-engineer addresses Critical/Major findings
5.  RE-VERIFY    → rebuild, retest
5b. BLAST-RADIUS → (conditional) check related files for contradictions/staleness
6.  SCORE        → quality-gates thresholds
7.  LOOP         → repeat 3-7 until the plan's fix-round budget is spent (default 5 when no plan declares one) → escalate
8.  PRESENT      → summary: files changed, issues found/fixed, score, open items; print REVIEW-ARTIFACT
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
REVIEW-ROUND: n=<n> budget=<b> scope=full   (scope=fix-diff is RESERVED, not available: scoped re-review is deferred)
ESCALATION: budget=<b> rounds_used=<n> reason=<one line>
REVIEW-ARTIFACT: round=<n> path=<path> findings=<c/m/n> agents=<returned>/<launched> converged=<yes/no>
SCORE: <n>/100 (threshold: <t>, gate: commit|pr|excellence[, evidence: <bundle-path>])
```

A SCORE is a judge verdict, valid only alongside fresh computational evidence: a successful test/lint/build run after the last source edit (`score-evidence-guard` enforces this). If VERIFY ran inside a subagent, say so when reporting.

Every REVIEW round prints `REVIEW-ROUND:` before its findings, and `n` counts **fix rounds** (`total_fix_rounds`: every REVIEW→FIX cycle AND every UAT→FIX cycle), not review ordinals, so it is the same number the plan's Budget bounds. Past the budget the next line is `ESCALATION:` (step 7), never another round; the escalation is a literal because a prose match let ordinary review text ("privilege escalation") disarm the gate. Reviewers launch in background and are joined at Finding Consolidation, so `agents=<returned>/<launched>` must balance before a SCORE: an unreturned reviewer is not a clean one.

`review-budget-guard` makes both invariants **countable, not enforced**: every line it reads is written by the same session whose turn it gates, so omitting the literals or under-reporting passes silently. It catches the honest failure (nobody was counting), which is the one the measurement found; it is not a control and a green run from it is not assurance.

## Invariants

- Review agents are read-only **with respect to the main working tree**: every launch carries `isolation: "worktree"`, so the writes empirical review needs (probes, mutation runs) land in the agent's own copy. The `.git` database is shared, so shared git state (branches, stash, config, hooks) stays untouched. Prose, not enforcement: nothing checks the parameter, a launch that omits it puts a write-encouraged reviewer in the real tree, and the definitions fail closed on their side. Isolation, not permission: it bounds contamination, it does not prevent prompt injection. software-engineer is read-write, scoped to its assigned files.
- The orchestrator is the sole committer. pi never commits, never takes a review or spec role (rules, agents and skills are spec), and every pi-executed subtask gets a DRIFT check.
- Fix-round ceiling, writer concurrency and finalization evidence come from the plan's Budget (plan-first-workflow). Hitting a limit means escalate; it never means stop quietly with a fluent summary.
