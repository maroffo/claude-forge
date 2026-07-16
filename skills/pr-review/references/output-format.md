# ABOUTME: The final report structure pr-review emits in Phase 7.
# ABOUTME: Extracted from SKILL.md; severities use the Critical/Major/Minor vocabulary from quality-gates.

# PR Review Output Format

```markdown
# PR Review: <title>

**Branch**: <head> -> <base>
**Scope**: <additions> additions, <deletions> deletions, <files> files, <commits> commits
**Score**: <N> (<gate status>)
**Reviewers**: <delegated agents + Gemini segments + second-opinion if it ran>
**Hallucinations caught**: <count> (<brief description>)

## Commit Narrative
<How the PR evolved: review-fix cycles, intentional deferrals>

## Critical (auto-fail)
<Table: #, Finding, File:Line, Introduced in, Fix attempted?, Evidence, Source>
<Evidence: `demonstrated (test)` / `pre-existing (test)` / taxonomy type (CWE, Big-O, convention, principle). Per finding with a red-green test: collapsible block with the test body and the failing output, copied from the clone before cleanup.>

## Major
<Table: #, Finding, File:Line, Commit context, Evidence, Source>

## Minor
<Summary count + notable items>

## Reclassifications (commit context)
<Table: Finding, Original severity, New severity, Reason>

## Unproven claims
<Claims whose red-green test did not fail: what was claimed, the passing test, second-opinion verdict (dropped / kept with new evidence / pending). Dropped ones also count in the header's "Hallucinations caught".>

## Dependencies
<CVE count, new deps, license status>

## Process Observations
<Scope concern, commit hygiene, review-fix pattern quality>

## Recommendation
<APPROVE / FIX BEFORE MERGE / REJECT AND SPLIT; if split, propose the breakdown>
```
