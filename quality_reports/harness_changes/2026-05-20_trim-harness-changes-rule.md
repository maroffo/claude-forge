# ABOUTME: Change contract for trimming rules/harness-changes.md to reduce always-on token cost
# ABOUTME: Preserves the rule's required signal, drops prose justification

# Harness Change Contract: trim `rules/harness-changes.md` from 735 to ~350 tokens

## Component

`rules/harness-changes.md`.

## Failure mode targeted

Token baseline 2026-05-19 shows `rules/harness-changes.md` at 735 tokens, 12.7% of the always-on budget (5797 tokens). Roughly 400 of those tokens are prose justification ("Without a contract, a harness edit looks identical...", "The contract is the difference between drift and engineering.") and pointers that the model does not need to re-read every session. The same rule expressed as a structured list with the 6 required fields, the 🔴/🟡/🟢 scope, and the template path costs roughly half the tokens.

## Predicted improvement

- Rule shrinks to ~350 tokens (-52%).
- Always-on baseline drops from 5797 to ~5400 tokens (-7%).
- Per-session token saving stacks: 5 sessions per week × ~385 tokens saved × 4 weeks ≈ 8k tokens saved per month. Small but free.

## Invariants preserved

The trimmed rule must still answer, in this order:
1. **When required (🔴)**: hooks/, rules/, agents/, skills/SKILL.md trigger surface, settings*.json hook/permissions/env blocks.
2. **When optional (🟡)**: typos, ABOUTME tweaks, internal refactors without trigger-surface change, test-only additions.
3. **When skipped (🟢)**: app code, README, LEARNING.md, blog/, docs/.
4. **The 6 contract fields**: Component, Failure mode targeted, Predicted improvement, Invariants preserved, Falsification, Rollback.
5. **Process pointer**: copy TEMPLATE.md, commit alongside change, append Result row after 10-20 sessions, do not edit retroactively.

The "Why this is not optional" rhetorical section gets removed entirely. Any future reader who wants the rationale can read the paper (cited at the top) or the original commit body (`0c15723`).

## Falsification

- If 2 or more of the next 5 change contracts written omit a required field, the trim removed essential scaffolding. Restore the verbose version.
- If a developer asks "do I need a contract for X?" and the trimmed rule cannot answer, scope clarity was lost.
- If always-on token baseline does NOT drop by at least 350 tokens after the trim, the actual reduction was over-promised.

## Rollback

```bash
git revert <commit>
```

Affects: `rules/harness-changes.md`. No code changes, no skill changes.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 5 contracts written after the trim, 1 token baseline | rules/harness-changes.md went 735 to 435 tokens, a 300-token drop that falls short of the 350 promised; the behavioral falsifications held, with 5 of 5 following contracts carrying all six required fields | kept |

Verdict: pending.
