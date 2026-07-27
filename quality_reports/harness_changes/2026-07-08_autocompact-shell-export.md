# ABOUTME: Change contract for moving CLAUDE_AUTOCOMPACT_PCT_OVERRIDE to the shell environment
# ABOUTME: Targets the settings.json env block being silently ignored by autocompact logic

# Harness Change Contract: autocompact threshold via shell export (60%)

## Component

- `~/.zshrc` (workstation_setup repo, `zsh/.zshrc`): `export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=60` before the `cc`/`cca` launchers
- `~/.claude/settings.json` env block: value aligned 50 -> 60 (kept for subprocess visibility and documentation)

## Failure mode targeted

`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: "50"` sat in the settings.json env block since 2026-05-19 with zero effect: auto-compact fired at ctx:100% (Max, 2026-07-08). Root cause is upstream: the env block is visible to subprocess tool calls but not applied to the app's own autocompact logic (anthropics/claude-code issues #52390, #63186, open as of v2.1.204). The documented workaround is exporting the variable in the shell that launches claude.

## Predicted improvement

In sessions launched from a fresh shell after this change, auto-compact triggers at ~60% of the window instead of ~100% (observable: statusline ctx% at the moment the compact fires; the [compact-resume] hook message timestamps it). Sample: first 5 auto-compacts.

## Invariants preserved

- Threshold only moves EARLIER, never disables compaction (no DISABLE_AUTO_COMPACT / DISABLE_COMPACT).
- Value stays in one authoritative place (shell); the settings.json copy mirrors it and must be updated together.
- No change for sessions launched outside a login shell (cron, IDE) until they inherit the export.

## Falsification

If after 5 auto-compacts the trigger point is still ~100% (export also ignored, e.g. issue #70477 remote-session path), the workaround is dead: remove the export and fall back to watcher-driven manual /compact. Also revert if 60% proves too aggressive (compacts more than ~2x per long session).

## Rollback

Delete the export block from `workstation_setup/zsh/.zshrc` and restore `"50"` in `~/.claude/settings.json`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 19 days live, 0 compacts with recorded occupancy | insufficient data: the export is in place in both workstation_setup/zsh/.zshrc:191 and ~/.zshrc:191 with settings.json aligned to 60, and subprocesses do read it since context-watcher derives its bands from 60, but nothing on disk records the ctx percentage at the moment a compact fires so whether the app itself honours the export is still unobserved; re-check needs the compact-resume hook to log occupancy | kept |
