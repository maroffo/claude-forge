# ABOUTME: Change contract for moving rarely-read sections of large skills into references/
# ABOUTME: Source: "The new rules of context engineering for Claude 5 generation models" (claude.com blog), rule 3

# Harness Change Contract: large skill bodies keep only what the normal path needs

## Component

Five skills, eight sections moved into `references/` with a one-line pointer left in place:

| Skill | Moved | Repo |
|---|---|---|
| `advanced-review` | Troubleshooting, Step 5b SonarQube (opt-in), Full-Repository Mode | `claude-advanced-review` (symlinked) |
| `second-opinion` | Prerequisites, Troubleshooting | claude-forge |
| `harness-trace` | Trace Schema (v2), Architecture, Common Issues | claude-forge |
| `test-design-reviewer` | Deterministic Scoring Calculator, Common Issues | claude-forge |
| `issue-loop-hikma` | Common issues | `claude-hikma-skills` (symlinked) |

No frontmatter was touched: descriptions control routing and had to stay identical for the routing eval to remain comparable.

## Failure mode targeted

A SKILL.md is loaded whole the moment the skill activates. Setup steps, troubleshooting lists, full schemas and opt-in modes are consulted rarely, yet they were paid for on every activation: `advanced-review` charged 2458 words to answer a review request, of which 680 were troubleshooting and an opt-in SonarQube path skipped by default.

## Predicted improvement

Per-activation cost of the five skills drops measurably with no loss of content: advanced-review 2458 -> 1784 (-27%), harness-trace 1100 -> 580 (-47%), second-opinion 1294 -> 1065, test-design-reviewer 1267 -> 1112, issue-loop-hikma 1338 -> 1195. Over the next 10 uses of these skills, none of them needs to open a `references/` file to complete its normal path.

## Invariants preserved

- Content is conserved, not deleted: measured per skill as body + new references vs the original, deltas between +35 and +99 words, all of it ABOUTME headers and pointer lines.
- Every `description:` field is byte-identical: routing behaviour must not move, and the routing eval baseline (40/40 on the frozen adversarial set) must stay comparable.
- The pointer keeps the original heading, so a reader looking for "Troubleshooting" still finds the heading where it was.
- Each new references file carries the 2-line ABOUTME header `make check` enforces.

## Falsification

If, over the next 10 uses of these five skills, a run has to open a `references/` file to complete its NORMAL path (not troubleshooting, not the opt-in mode), the split cut into the working flow: move that section back.

Second falsifier: if a session reports missing information that was in the body before (for instance running advanced-review without SonarQube awareness when it was requested with `--sonarqube`), the pointer is not discoverable enough: inline a one-line summary next to it.

## Rollback

Three repos, three reverts: `git revert <commit>` in claude-forge for second-opinion / harness-trace / test-design-reviewer, in `claude-advanced-review` on branch `feat/progressive-disclosure`, and in `claude-hikma-skills` for issue-loop-hikma.

Note for future scoping: `advanced-review` and `issue-loop-hikma` are symlinks into separate repositories. A brief that names skills by path can silently cross repository boundaries; check `ls -la skills/` before scoping one.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 2 traced sessions since merge, of a 10-use window across 5 skills | insufficient data: the split is in place across all three repos and no run has reported having to open a references/ file on its normal path, but with only 2 traced sessions the 10-use window has barely started and neither falsifier has had a chance to fire; the per-activation word savings were measured at authoring time and are not re-derived here | kept |
