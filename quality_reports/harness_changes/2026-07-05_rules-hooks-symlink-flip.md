# ABOUTME: Change contract: deployed rules/ and forge-derived hooks become symlinks into the repo
# ABOUTME: Extends the one-skill-tree model to the last two copy-synced surfaces (rules, hooks)

# Harness Change Contract: rules and hooks symlink flip

## Component

Runtime deployment (machine-local, gitignored paths in workstation_setup): `~/.claude/rules` becomes a directory symlink to `claude-forge/rules`; each forge-derived file in `~/.claude/hooks/` becomes a per-file symlink to `claude-forge/hooks/<file>`. Machine-local hook content (ClaudeNotifier.app, notify.sh) stays a real file. Repo side: this contract only; no code change (the installer copy model for other users is untouched).

## Failure mode targeted

Rules and hooks are the last copy-synced deploy surfaces after the 2026-07-04 one-skill-tree flip ([[2026-07-04_one-skill-tree]]). Observed 2026-07-05: 3 of 5 deployed rules were stale (orchestrator-protocol missing the Score Reporting section merged the same day, plan-first-workflow missing ExecPlans, quality-gates missing Severity Vocabulary), silently running sessions on outdated governance. Same drift class the skills flip eliminated.

## Predicted improvement

Zero rules/hooks drift by construction: every merge to forge main is live immediately. The manual re-sync step (memory gotcha "re-run cp hooks/* after merges") disappears.

## Invariants preserved

- Per-file symlinks for hooks: the hooks directory stays real so machine-local, non-forge content (ClaudeNotifier.app, notify.sh) is untouched and settings.json hook paths stay valid.
- Old copies preserved at `~/.claude/rules.backup/` and `~/.claude/hooks.backup/` (same pattern as skills.backup).
- Verified pre-flip: deployed hook copies were byte-identical to forge main (no local edits lost).
- workstation_setup git state untouched: all flipped paths are gitignored there.
- Known trade-off (inherited from one-skill-tree's falsification clause): an unmerged forge branch checkout changes live rules/hooks mid-session.
- Per-file model gotcha: a hook file NEWLY added to forge needs a one-time `ln -s $FORGE/hooks/<f> ~/.claude/hooks/<f>` after merge (directory symlink was rejected: the hooks dir holds machine-local non-forge content). Existing hooks update live with no action.

## Falsification

A live session breaks or behaves inconsistently because a forge branch checkout swapped rules/hooks under it, with impact worse than the drift class this removes: revert to copies plus a freshness-check deploy script.

## Rollback

`rm ~/.claude/rules && mv ~/.claude/rules.backup ~/.claude/rules; for f in ~/.claude/hooks.backup/*; do ln -f "$f" ~/.claude/hooks/; done` (or copy back). One line per surface, no git involved.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 22 days live (2026-07-05 to 2026-07-27) | ~/.claude/rules is a directory symlink into the forge and every forge-derived hook is a per-file symlink, so rules and hooks drift is impossible by construction, backups preserved at rules.backup and hooks.backup, and no session breakage from a branch checkout swapping rules mid-run was recorded | kept |
