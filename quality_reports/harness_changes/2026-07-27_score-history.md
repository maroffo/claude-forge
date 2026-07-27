# ABOUTME: Change contract for the /score history log (scripts/score-log.sh + skills/score/SKILL.md)
# ABOUTME: Failure mode targeted: no cross-session quality trend, so regressions between sessions stay invisible

# Harness Change Contract: score history log for /score

Plan: `quality_reports/plans/active/2026-07-27_gstack-borrowings.md`, workstream W4 (decision 9, second-opinion requirement 6). Borrowed from gstack's `health` skill, with its stated caveat fixed: there, the model does the arithmetic and the append; here a script does both.

## Component

- `scripts/score-log.sh` (new, executable): append mode and `--trend` mode.
- `skills/score/SKILL.md`: new `## History` section plus one process step; frontmatter description untouched (trigger surface unchanged).
- `Makefile`: `lint-shell` shellcheck list gains the new script.
- `scripts/tests/test_score_log.py` (new): E2E matrix rows 8-9.

## Failure mode targeted

`/score` reports a point-in-time number and nothing else. SCORE events land in the per-session harness-trace JSONL, but no cross-session view exists, so a quality regression between sessions on the same branch is invisible: a run scoring 71 today reads exactly like a run scoring 71 after three sessions at 95. Observed as a gap during the 2026-07-27 gstack analysis (`skills/score/SKILL.md` had no history surface; verified by grep, zero hits).

## Predicted improvement

Every `/score` invocation from now on leaves a machine-written row, and the trend table makes a drop visible at the moment it happens rather than at retrospective time. Numerically: after 20 `/score` runs, `quality_reports/score-history.jsonl` holds 20 rows that reconcile 1:1 with the `SCORE:` events in the same sessions' traces, and at least one score drop between consecutive runs on the same branch is noticed in-session (the observation that today has no surface at all).

## Invariants preserved

- The model never computes the timestamp, the row, or the delta. It passes six measured values; the script writes and computes. A hand-written row is a regression even if its content is correct.
- The history file never enters git history in any repo: the gitignore guard appends the path exactly once, append-only, and never rewrites the target repo's `.gitignore`.
- A logging failure never blocks the gate. `/score` reports its number even when the script is missing or errors.
- Read-only invocation stays read-only: `--trend` with no history creates no directory, no `.gitignore`, and exits 0.
- The history is written to the git root of the repo being scored, never to claude-forge when `/score` runs elsewhere.
- Invalid input writes nothing (exit 2 before any file touch).

## Falsification

Any of these means revert:

1. **Divergence.** In a session that ran `/score`, the rows appended to `quality_reports/score-history.jsonl` do not match the `SCORE:` events in that session's harness trace (missing row, duplicate row, different number). The file is a denormalized view; a view that disagrees with its source is worse than no view.
2. **Corruption.** `--trend` reports skipped unparseable lines on a file only this script wrote.
3. **Unused.** After 20 sessions, the trend output was never consulted in any decision (no session log or transcript references it). A log nobody reads is cost without signal: drop the script and keep the trace.
4. **Leak.** The history file appears in any repo's `git log`, meaning the guard failed or was bypassed.

## Rollback

`git revert <commit>`. Affects: `scripts/score-log.sh`, `scripts/tests/test_score_log.py`, `skills/score/SKILL.md`, `Makefile`. Already-written history files are local and gitignored: delete with `rm quality_reports/score-history.jsonl` per repo, and drop the two `.gitignore` lines the guard appended.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
