# ABOUTME: Change contract for adding crap4go and gremlins output as Finding Contract evidence forms
# ABOUTME: Two advisory Go make targets, no new rubric row, no threshold anywhere

# Harness Change Contract: crap4go and gremlins output as evidence forms, not gates

## Component

- `skills/project-checks/templates/go.mk` (new `crap` and `mutation` targets, both outside `check`)
- `rules/quality-gates.md` (Finding Contract: two evidence forms added)
- `skills/test-design-reviewer/SKILL.md` (Tautology Theatre: surviving mutant admissible as evidence)
- `skills/project-checks/SKILL.md` (documents the two advisory targets)

## Failure mode targeted

Coverage and tautology findings rest on reviewer prose because no computational
check is available at review time. `make check` proves the suite is green, and
nothing in the harness distinguishes complex-and-tested from
complex-with-tests-that-assert-nothing. A SCORE is required to sit alongside
fresh evidence, but that evidence is only test/lint/build green, which a suite
of tautologies satisfies perfectly.

## Predicted improvement

Qualitative, since neither finding type is counted today. Coverage and
tautology findings can carry a crap4go line (CC, coverage, CRAP for the touched
function) or a surviving gremlins mutant as checkable evidence instead of an
argument. Smallest sample to detect it: the next 5 Go reviews where a coverage
or tautology finding is raised at all; if none of them cites either artifact,
the affordance is not being reached for.

## Invariants preserved

- `make check` stays byte-identical: `lint vet fmt-check vuln test`, same recipes.
- No threshold enters the rubric. CRAP = CC^2*(1-cov)^3 + CC, so full coverage
  zeroes the first term and CRAP >= CC always; a fixed CRAP limit T is silently
  a cyclomatic-complexity gate at CC > T (a 99%-covered parser with CC=35 scores
  CRAP 35.001 and would be misfiled as "missing test coverage").
- Mutation testing never runs in the inner loop or in `check`: it recompiles and
  reruns the suite once per mutant. Advisory target, invoked on suspicion.
- No new severity row in the scoring rubric. Both artifacts are evidence for
  existing severities, not a new deduction category.

## Falsification

A review cites a CRAP number (or a mutation score) as the finding itself rather
than as evidence for a named defect: "CRAP is 130 on Widget.Run" with no claim
about what is untested or wrong. That is the metric-as-gate failure the framing
was meant to prevent, so if it appears, revert. Same verdict if `crap` or
`mutation` shows up as a `check` prerequisite in any generated Makefile.

## Rollback

`git revert <W3 commit>`. Affects: skills/project-checks/templates/go.mk,
rules/quality-gates.md, skills/test-design-reviewer/SKILL.md,
skills/project-checks/SKILL.md, and this contract.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
