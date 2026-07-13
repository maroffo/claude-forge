# ABOUTME: Change contract for the plan-forge skill (issue/analysis to ExecPlan + implementation prompt + /goal line)
# ABOUTME: Codifies the delivery-prep playbook proven on hikma-mirsad#576 and the model-manifest task (2026-07-12/13)

# Harness Change Contract: plan-forge skill

## Component

New skill: `skills/plan-forge/` (SKILL.md + references/plan-template.md + references/impl-prompt-template.md). Registrations: `skills/_INDEX.md` row, `CLAUDE.md.example` skills-table row. The SKILL.md description controls auto-triggering.

## Failure mode targeted

The issue-to-implementation prep playbook (deep code analysis, second opinion, ExecPlan on disk, delegation prompt + /goal) gets re-improvised from memory each time. Observed across 2026-07-12/13 sessions: when improvised, steps drop or degrade silently: the second opinion gets skipped, REPRODUCE-first gets forgotten for bugfixes, E2E matrices come out thin or combinatorial, the emitted /goal line misses the canonical SCORE format the evaluator keys on, and the shared-worktree git guards (no checkout/pull/--amend) are omitted from subagent briefs, each omission having already caused a real incident.

## Predicted improvement

Every eligible task (issue or in-session analysis, non-SKIP_SET) prepped through one command produces a structurally complete plan (locked decisions, W0 REPRODUCE for bugfixes, exhaustiveness-argued E2E, DoD with SCORE gate) and a prompt/goal pair that needs no structural rework. Qualitative; evaluate over the next ~10 uses. Baseline: today 0 plans are template-derived; each one is hand-assembled.

## Invariants preserved

- The skill only PLANS: it writes a plan file and emits text; it never implements, never opens PRs, never pushes, never sets /goal itself (only the user can).
- No behavior change for any existing skill or rule; plan-first-workflow and orchestrator-protocol stay authoritative (the skill operationalizes them and cross-references, it does not fork their content).
- Second-opinion skip is explicit and stated, never silent.
- Trigger surface is additive: description triggers on plan-specific phrases (plan-forge, issue to plan, prepara il piano); it must not swallow requests meant for `adr`, `refine-requirements`, or direct implementation asks.

## Falsification

Revert or rewrite if, over the next 10 uses, ANY of:
- more than 3 emitted plans/prompts need structural rework (missing mandatory section, malformed /goal line, wrong verify commands) before they can drive a session, or
- the skill auto-triggers on requests that were not plan-prep (swallowing adr/refine-requirements/implementation asks) more than twice, or
- it goes unused for 10 consecutive eligible tasks (people keep improvising: the ergonomics failed).

## Rollback

`git revert <commit>`. Affects: `skills/plan-forge/` (3 files), `skills/_INDEX.md`, `CLAUDE.md.example`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
