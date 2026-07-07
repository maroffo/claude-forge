# ABOUTME: Change contract — scheduled propose-only mode for knowledge-sync (monthly crontab)
# ABOUTME: Targets vault-to-skills sync never happening because cadence relied on human memory

# Harness Change Contract: knowledge-sync Scheduled Mode

## Component

Skill: `skills/knowledge-sync/SKILL.md` (new "Scheduled Mode" section, reworded autonomy line). Settings-adjacent system state: one user crontab entry, documented verbatim in the skill and **installed manually by Max** (the auto-mode classifier correctly blocked Claude from persisting a headless autonomous run). Plus cadence-drift fix in `~/.claude/CLAUDE.md` (weekly → monthly, matching the skill's own text).

## Failure mode targeted

The vault-to-skills sync never runs: its cadence ("run weekly/monthly") relied on human memory, and CLAUDE.md ("weekly") contradicted the skill ("monthly"). No sync report has a mechanical trigger.

## Predicted improvement

A propose-only report appears in `quality_reports/knowledge_sync/` at least 1st-of-month + manual-kick coverage: ≥ 1 report per month over the next 3 months, versus ~0 sync runs in recent history.

## Invariants preserved

- APPLY never runs unattended: the scheduled prompt explicitly stops at PROPOSE; the skill's "never auto-apply" rule is untouched.
- `learning-loop` stays unscheduled (its "never autonomously" stance is deliberate and out of scope here).
- One cadence source of truth: skill says monthly, CLAUDE.md and CLAUDE.md.example now agree.

## Falsification

If a scheduled run ever edits a skill file (APPLY leak), delete the crontab entry immediately and revert the Scheduled Mode section. If 3 consecutive monthly runs produce empty or failed reports (see cron log), the automation isn't paying for itself: remove the crontab, keep the documented manual kick.

## Rollback

`git revert <commit>` (affects `skills/knowledge-sync/SKILL.md`); `crontab -r` (or remove the single entry); restore "weekly" line in `~/.claude/CLAUDE.md` (outside git).

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
