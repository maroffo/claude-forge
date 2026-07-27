# ABOUTME: Change contract for adding downward boundaries to three skill descriptions that over-trigger on trivial work
# ABOUTME: Backed by a per-case routing eval, baseline 37.7/40 -> 40/40; includes the honest limits of that evidence

# Harness Change Contract: three descriptions stop volunteering for trivial work

## Component

The `description:` frontmatter of `skills/releasing-software/SKILL.md`, `skills/rails/SKILL.md` and `skills/orchestrator/SKILL.md`. Descriptions are the routing surface, so this is a trigger-surface change.

Bodies untouched. Total added: 62 words across three descriptions.

## Failure mode targeted

Skills volunteer for work that needs no skill. Measured with a per-case routing eval over the live descriptions (`scripts/skill-routing-eval.py run`, one judge call per case, 40 adversarial cases, judge gemini-3.6-flash):

| Case | Chose | Frequency |
|---|---|---|
| "aggiorna la versione dentro package.json" | `releasing-software` | 3/3 runs |
| "questa migration mi blocca la tabella in produzione" | `rails` | 2/3 runs |
| "aggiungi un campo al DTO e propagalo" | `orchestrator` | 2/3 runs |

All three are SKIP_SET-shaped edits. The `orchestrator` case is a regression introduced the same day by this very rework: its description said "load before step 1 of any task that is not in SKIP_SET", which reads as a candidate for any non-trivial task.

The fix is a downward boundary ("not for X, just do it"), not a boundary against sibling skills: the eval found zero confusion between siblings (review 7/7, knowledge 5/5, planning 3/3).

## Predicted improvement

Per-case routing accuracy on the frozen 40-case set rises from a 37.7/40 mean (37, 38, 38 across three runs) to 40/40, and holds across repeated runs. In real sessions, fewer skill loads on edits that need none.

## Invariants preserved

- Positive triggers are untouched: every "use when" clause stays exactly as it was, so the skills still fire on the work they own.
- Only descriptions change; no skill body, no rules file, no hook.
- The eval instrument, case set and judge model stay fixed across the before/after measurement, so the delta is attributable to the edit.

## Falsification

If any of the three skills stops firing when it genuinely applies (a release request that does not reach `releasing-software`, a Rails question that does not reach `rails`, an approved plan entering step 1 without the `orchestrator` skill), the boundary cut into the positive trigger: revert that description.

Counted form: over the next 10 sessions, more than one observed miss of this kind means revert.

## Limits of the evidence (read before trusting the numbers)

1. **The improvement is measured on the cases used to diagnose it.** The three fixed cases are the three the baseline failed. This is the classic overfitting setup, and the eval cannot rule it out.
2. **The holdout does not discriminate.** An 8-case holdout of never-seen over-trigger prompts scores 8/8 both before and after the change. It shows the edit caused no regression; it does NOT show the edit generalizes, because the pre-fix descriptions already passed it.
3. **The judge is a proxy.** Real routing is done by Opus in session, not by gemini-flash over a catalog. The per-case mode removes the batch-composition bias found earlier (a batch judge infers how many negatives to expect, and scored a misleading 40/40), but the absolute number is still not "how Claude Code routes".
4. What would settle it: holdout cases that the pre-fix descriptions actually fail, or over-triggering counted in real session traces.

## Rollback

`git revert <commit>`. Affects three `description:` lines in `skills/{releasing-software,rails,orchestrator}/SKILL.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 2 traced sessions since merge, of a 10-session window; the 40-case eval not re-run | insufficient data: all three boundaries are live in the descriptions and no genuine miss has been observed, but the real-session half is not measurable at all because a skill that did NOT fire leaves no trace, all 40 ROUTE events carry decision_basis "explicit subagent_type" with alternatives_considered empty; the eval half is worse than unmeasured, the pr-review round of the same day found the instrument was scoring the author's machine (3 of 40 cases expected gitignored symlink skills, unreachable on a clean checkout) and it was changed to fail loudly, so the 37.7 baseline is no longer comparable to a re-run | kept |
