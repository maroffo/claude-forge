# ABOUTME: Change contract for adding explicit scope modes to refine-requirements (Hold, Selective Expansion, Expansion, Reduction)
# ABOUTME: Borrowed from gstack plan-ceo-review minus its "completeness is cheap" premise; Hold stays the default

# Harness Change Contract: scope mode chosen explicitly at refinement time

## Component

`skills/refine-requirements/SKILL.md` body (new step 0 in `## Process`, two mode-conditional lines in step 3 and `## Anti-patterns`) and one line in the Requirements Refinement section of `rules/plan-first-workflow.md`.

The `description:` frontmatter is untouched, so the auto-trigger surface of the skill does not move.

## Failure mode targeted

Hold Scope is hardcoded, with no sanctioned path to deliberately explore scope at refinement time. `skills/refine-requirements/SKILL.md:26` ("if user suggests new scope, capture as deferred idea, redirect back") and `:34` ("clarify HOW to implement what's requested, not WHETHER to add more") make every refinement session a scope-holding session, including greenfield work where the useful question is what else belongs in the thing being started. The office-hours reframe (a session that widens the request on purpose, with the user opting in) has nowhere to happen: it is either not offered at all or smuggled in against the skill's own rule.

Source: gstack `plan-ceo-review` scope modes, studied 2026-07-27 (plan `quality_reports/plans/active/2026-07-27_gstack-borrowings.md`, decision 8). gstack's premise "COMPLETENESS IS CHEAP, boil the ocean" is deliberately NOT imported: the borrow is the mode choice, not the appetite.

## Predicted improvement

On greenfield and feature tasks, the mode question is asked once and answered; over the next 10 refinement sessions, at least one session picks a non-Hold mode and produces additions the user explicitly accepted (previously reachable only by breaking the skill's rule). On bugfix and refactor tasks the observable behavior is unchanged: zero mode questions asked.

Qualitative half, smallest sample to detect it: 10 refinement sessions, of which at least 3 are bugfix or refactor (to see the silent-Hold path exercised).

## Invariants preserved

- No silent scope change in any mode: every addition and every cut is individually opted in by the user.
- Hold Scope remains the default and the recommended option wherever the question is asked, and the only behavior when the task class is unclear.
- Declined proposals keep the existing destination: deferred idea, thread redirected back.
- The skill's `description:` frontmatter is byte-identical, so routing behavior is unchanged.
- Steps 1-4 of the refinement process (gray areas, AskUserQuestion, scope guard, decision capture) still run in every mode.

## Falsification

Either of these, observed in a refinement session, means the erosion the reviewers predicted has happened and the change reverts to hardcoded Hold:

1. The model proposes expansions unprompted while in Hold Scope (or on a bugfix or refactor, where no mode question is asked at all).
2. Two or more expansions are batched into a single question, or into one blanket "Selective Expansion accepted".

Counted form: over the next 10 refinement sessions, more than one occurrence of either means revert.

## Rollback

`git revert <commit>`. Affects: `skills/refine-requirements/SKILL.md` (step 0 and the two mode-conditional lines), `rules/plan-first-workflow.md` (one bullet under Scope discipline).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
