# ABOUTME: Change contract: SessionStart hook counting traced sessions against pending change contracts
# ABOUTME: Makes the 5/10-session contract checkpoints deterministic instead of relying on memory

# Harness Change Contract: checkpoint-reminder hook

## Component

Hook: `hooks/checkpoint-reminder.py` + `.sh` (new), registered in project-scoped `.claude/settings.json` (SessionStart) and documented in `hooks/settings.example.json`. Tests: `hooks/tests/test_checkpoint_reminder.py`.

## Failure mode targeted

Change contracts prescribe verification checkpoints ("after 5 orchestrator sessions check SCORE events", "after 10-20 sessions fill the Result row"), but nothing counts sessions: the checkpoint depends on a human remembering an ordinal, not a date. Observed: all 19 pre-2026-07-05 contracts have empty Result tables; none was ever closed on schedule. Rules are prose; hooks make them deterministic (CLAUDE.md enforcement-layer principle).

## Predicted improvement

The 4 contracts dated 2026-07-05 get their checkpoints surfaced automatically: a SCORE spot-check nudge at 5 traced sessions, a Result-row + /harness-mechanic nudge at 10. Success metric: their Result rows are filled within 15 sessions of authoring (against a 0/19 historical base rate).

## Invariants preserved

- Fail-open: any error exits 0 silently; a broken reminder never blocks a session.
- Self-silencing: filling the Result rows (the desired behavior) is exactly what stops the nag; no state files.
- Scoped to repos with `quality_reports/harness_changes/` + `traces/`; inert everywhere else.
- Same-day traces do not count as evidence (they authored the contract); TEMPLATE.md ignored.
- Registered project-side, not in user settings: other repos see no new hook. If the example block is later merged into user settings, forge sessions would print the reminder twice (cosmetic only).

## Falsification

Reminder fires in a repo with no pending contracts or before 5 post-contract sessions (noise), OR the 2026-07-05 contracts still have empty Result tables after 20+ traced sessions with the reminder firing (nudge ignored, mechanism useless): either way, unregister and revert.

## Rollback

`git revert <commit>`; the hook self-unregisters because `.claude/settings.json` is part of the same commit.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 12 traced sessions since 2026-07-05 | hook observed firing at SessionStart on 2026-07-27 and the Result-row pass it nudges for (issue #103) is running at session 12 of the contracted 15, against a 0-of-19 historical base rate; the falsification needs 20+ post-contract traced sessions and only 12 exist | kept |
