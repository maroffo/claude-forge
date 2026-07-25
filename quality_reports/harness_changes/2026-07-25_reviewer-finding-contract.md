# ABOUTME: Change contract for the Finding Contract: review agents must name the evidence that settles each finding
# ABOUTME: Source: Graph Engineering note (July 2026) §VI-D, "a reviewer returns criterion-level defects, not looks good"

# Harness Change Contract: reviewer findings carry required evidence

## Component

`rules/quality-gates.md` (new `## Finding Contract` section) and the seven review agent definitions: `agents/{architecture,security,performance,database,dependency,dx,test}-reviewer/AGENT.md`.

In each agent, the re-inlined line `- Severity: CRITICAL / MAJOR / MINOR` is replaced by a pointer to the contract, and every finding line of the Output Format template gains a trailing `| evidence: [observation that settles it]` field.

## Failure mode targeted

Reviewers return findings that cannot be mechanically checked. A finding states a claim and a fix but never names the observation that would settle whether it is real or whether the fix worked, so the FIX round argues from prose instead of verifying, and the two-confirmation gate at SCORE has nothing to key on except "tests pass". The Graph Engineering note names the same failure at handoff boundaries: an evaluator that returns free-form critique instead of criterion-level defects with `required_evidence`.

## Predicted improvement

Over the next 10 traced sessions that run the REVIEW step: at least 80% of reported findings carry a non-placeholder `evidence:` field, and `total_fix_rounds` per session does not increase (findings that cannot name evidence are dropped at the reviewer, so fewer arguable findings enter FIX). Secondary, non-numeric: the same reviewers stop re-inlining the severity vocabulary, so `quality-gates.md` becomes the only place it exists (7 copies removed).

## Invariants preserved

- Review agents stay read-only.
- The severity vocabulary stays defined once, in `quality-gates.md`; no agent re-inlines it.
- Net word count of the seven agent definitions does not grow (the pointer replaces the severity line; the evidence field extends existing template lines).
- Precision over recall is unchanged: a reproducible, reachable bug is never dropped for being "obvious". The contract drops findings with no nameable evidence, not findings that are inconvenient.

## Falsification

If, over the next 10 REVIEW-running sessions, reviewers systematically emit the literal placeholder `evidence: [observation that settles it]` (template echoed, not filled) in more than 20% of findings, the field is decoration and the change failed: revert.

Second falsifier: if a real CRITICAL is observed being suppressed with the rationale "no evidence nameable", the drop rule is harming recall: revert the drop rule (keep the field).

## Rollback

`git revert <commit>`. Affects: `rules/quality-gates.md`, `agents/{architecture,security,performance,database,dependency,dx,test}-reviewer/AGENT.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
