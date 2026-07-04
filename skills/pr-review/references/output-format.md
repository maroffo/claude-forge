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
<Table: #, Finding, File:Line, Introduced in, Fix attempted?, Source>

## Major
<Table: #, Finding, File:Line, Commit context, Source>

## Minor
<Summary count + notable items>

## Reclassifications (commit context)
<Table: Finding, Original severity, New severity, Reason>

## Dependencies
<CVE count, new deps, license status>

## Process Observations
<Scope concern, commit hygiene, review-fix pattern quality>

## Recommendation
<APPROVE / FIX BEFORE MERGE / REJECT AND SPLIT; if split, propose the breakdown>
```
