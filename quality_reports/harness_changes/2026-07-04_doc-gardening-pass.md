# ABOUTME: Change contract for the doc-gardening pass (deterministic stale-reference scan + agent judgment pass in learning-loop)
# ABOUTME: Failure mode = governance docs rot silently and keep steering sessions with stale claims

# Harness Change Contract: doc-gardening pass in learning-loop

Authored before landing. Linked from the commit body. Append-only after merge. Imports the recurring "doc-gardening agent" practice from OpenAI's harness-engineering post (a monolithic instruction file "rots instantly... and the file quietly becomes an attractive nuisance").

## Component

New script: `scripts/doc_gardening.py` + `doc-garden` Makefile target. Skill edit: `skills/learning-loop/SKILL.md` (new "Doc-gardening pass" section, description gains doc-gardening trigger phrases: this changes the auto-trigger surface).

## Failure mode targeted

Governance docs (CLAUDE.md tables, rules/, SKILL.md files) drift from reality with no detection: a rule references a renamed file, the skills table routes to a deleted skill, a SKILL.md claim is contradicted by a later change contract. Because these docs are injected into every session, stale claims actively steer Claude wrong, and nothing in the harness ever re-reads them for freshness (learning-loop mines failures, harness-mechanic mines traces; neither audits the docs).

## Predicted improvement

Baseline measured at landing: 0 dead paths, 0 missing-skill table rows across 60+ governance docs (clean start), 14 advisory unlisted skills. Prediction: over the next 3 monthly runs, the scan catches at least one real dead reference introduced by normal harness churn before it misleads a session, and the repo baseline stays at 0 findings after each run.

## Invariants preserved

- Deterministic phase is read-only, stdlib-only, no LLM, no network, exit-code contract (0 clean / 1 findings) suitable for future CI gating but NOT wired into `make check` yet (a noisy gate trains people to bypass it; it must earn that promotion via a separate contract).
- Learning-loop remains human-cadence only, never autonomous.
- UNLISTED-SKILL stays advisory: an unlisted skill is not a defect (skills auto-trigger from their own descriptions).
- The skill's existing trigger phrases and anti-goals are unchanged; only additive.

## Falsification

If over 3 runs the scan reports only advisory noise and zero true dead references while a real stale-doc incident (a session misled by an outdated rule or table) happens anyway, the check is looking at the wrong layer: the value was in the agent judgment pass, and the deterministic scan should be folded into check_repo or dropped. Also falsified if MISSING-SKILL/DEAD-PATH produce recurring false positives that need per-run suppression.

## Rollback

`git revert <commit>`. Affects: scripts/doc_gardening.py, Makefile, skills/learning-loop/SKILL.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
