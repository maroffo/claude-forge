# ABOUTME: Change contract for the Depth column and COVERAGE footer on the plan-forge E2E matrix
# ABOUTME: Borrowed from gstack plan-eng-review depth stars; prompt-only by decision 7, no validator in v1

# Harness Change Contract: test depth is visible in the plan's E2E matrix

## Component

`skills/plan-forge/references/plan-template.md`: the `## E2E matrix` section gains a `Depth` column with the star legend inline and a computed `COVERAGE: n/m paths (p%)` footer (both mandatory wherever the matrix appears), a `### Path trace` subsection recommended for complex-verdict plans only, one DoD line, and one bullet in `## Hard-won rules baked into this shape`.

`skills/plan-forge/SKILL.md`: one line in the step 3 non-negotiables stating the same mandate next to the existing exhaustiveness note. The `description:` frontmatter is untouched, so the auto-trigger surface of the skill does not move.

## Failure mode targeted

The E2E matrix records scenario and assertion but not test DEPTH (`skills/plan-forge/references/plan-template.md:50-55` before this change): a smoke test and a full behavior + edge + error test are indistinguishable rows. An 18-row matrix where twelve rows are greps therefore reads, to the reviewer approving the plan and to the implementing session executing it, exactly like an 18-row matrix that exercises real behavior. Thin coverage hides behind row count, and it hides at the one moment it is still cheap to fix, before implementation starts.

Nothing in forge asked for depth anywhere: `grep -ri 'diagram\|mermaid'` over `skills/plan-forge/`, `skills/orchestrator/SKILL.md` and `rules/plan-first-workflow.md` returned zero hits on 2026-07-27.

Source: gstack `plan-eng-review` depth stars and computed coverage line, studied 2026-07-27 (plan `quality_reports/plans/active/2026-07-27_gstack-borrowings.md`, decisions 6 and 7). gstack's full ASCII test-coverage diagram is folded INTO the matrix rather than added beside it: two artifacts describing the same paths drift apart, and the diagram is the one that stops being updated.

## Predicted improvement

Over the next 10 test-heavy plans, every matrix carries a filled Depth column and a computed COVERAGE footer, and at least 2 of those plans have their row mix visibly challenged at approval time (a row moved from 1★ to 3★, or a `[GAP]` row added) before implementation starts. The counted form is the falsification below, inverted: 0 or 1 plans out of 10 missing the column or the footer.

Smallest sample to detect it: 10 plans with an E2E matrix. Plans without a matrix (non-test-heavy) are outside the sample and are not failures.

## Invariants preserved

- The exhaustiveness note keeps its job: Depth is per-row quality, the note is still the union argument for which rows exist at all. Neither replaces the other, and a high COVERAGE ratio over a thin union is still a thin matrix.
- The path trace stays RECOMMENDED and complex-verdict only. Making it mandatory for every plan is the ceremony the second opinion warned about.
- Mermaid remains available for architecture diagrams; ASCII is prescribed for the path trace specifically, for diffability.
- No validator, hook or check script ships with this change (decision 7): the DoD slot and human plan approval are the only pressure in v1.
- The `description:` frontmatter of plan-forge is byte-identical, so routing behavior is unchanged.
- The plan skeleton stays copy-pasteable: the added table and trace are placeholders, not content the author must argue with.

## Falsification

Two or more of the next 10 test-heavy plans ship with the Depth column empty or the COVERAGE footer absent. That means the prompt-only device decayed exactly the way both reviewers predicted a slot-only mandate would, and the response is not to re-word the template: build the presence-check hook recorded in `quality_reports/plans/tech-debt.md` (a PostToolUse or plan-approval check that greps the written plan for the column header and the `COVERAGE:` line).

Secondary, weaker signal to watch on the same sample: every row in a matrix carries the same star rating. Uniform depth is either an honest property of that task or the column being filled in as a formality; check the plan, do not count it automatically.

## Rollback

`git revert <commit>`. Affects: `skills/plan-forge/references/plan-template.md` (E2E matrix section, path trace subsection, one DoD line, one hard-won-rules bullet), `skills/plan-forge/SKILL.md` (one line in the step 3 non-negotiables).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
