# ABOUTME: Change contract for disambiguating review-family triggers and completing the routing table
# ABOUTME: Failure mode = "ask gemini to review" can load the wrong skill; heavy review tiers invisible in CLAUDE.md

# Harness Change Contract: review-family trigger boundaries

Authored before landing. From the 2026-07-04 skill/hook audit (workflow MODERATE trigger overlap + MINOR stale table).

## Component

Skill descriptions (trigger surface): `skills/second-opinion/SKILL.md` (decision/diagnosis phrasing, explicit negative trigger for 'ask gemini to review'), `skills/cloud-infrastructure/SKILL.md` (explicit HCL-mechanics-vs-architecture boundary with terraform). Routing table: `CLAUDE.md.example` (adds advanced-review, score, project-checks rows; relabels second-opinion as Claude+Gemini+DeepSeek).

## Failure mode targeted

Overlapping trigger phrases route to the wrong skill: "ask Gemini to review my changes" matched both second-opinion ("ask gemini") and gemini-review ("review code"), and an IAM-policy-in-HCL request matched both terraform and cloud-infrastructure with no stated boundary. Meanwhile the heaviest review tier (advanced-review) was absent from the CLAUDE.md routing table, making the most capable tool the least discoverable.

## Predicted improvement

Review-phrased requests land on gemini-review; decision/diagnosis-phrased requests land on second-opinion; the routing table names all three review tiers. Checkable over the next 10 review-ish requests: zero wrong-skill loads.

## Invariants preserved

- second-opinion keeps its Docker/three-reviewer behavior and its auto-trigger rules in CLAUDE.md; only the description wording changed.
- "ask deepseek"/"ask gemini" still route to second-opinion when about a decision or approach.
- No skill renamed, no skill removed.

## Falsification

If Max says "second opinion on this diff" style phrases and lands on gemini-review (or vice versa) more than once in 10 uses, the boundary is drawn on the wrong axis (tool-name vs intent): redraw on artifact type (diff/PR vs decision) instead.

## Rollback

`git revert <commit>` restores the previous descriptions and table.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
