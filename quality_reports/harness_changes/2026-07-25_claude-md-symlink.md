# ABOUTME: Change contract for symlinking the installed CLAUDE.md to the repo copy, plus the installer guards that protects it
# ABOUTME: Targets the drift between ~/.claude/CLAUDE.md and CLAUDE.md.example observed on 2026-07-25

# Harness Change Contract: installed CLAUDE.md is a symlink, and the installer respects it

## Component

- `~/.claude/CLAUDE.md`: was a copy, now a symlink to `claude-forge/CLAUDE.md.example` (local configuration, not a repo file).
- `install.sh`: two guards, one at the copy step and one in `replace_in_installed`, both keyed on `[[ -L ]]`.

## Failure mode targeted

The single most important always-on file was maintained in two places and had already diverged: on 2026-07-25 the installed copy listed `mauro-blogger` while the repo copy listed `issue-loop-wishew`. Every harness change that edited only the repo copy never reached the running agent, silently. `rules/`, `skills/` and `agents/` were symlinked long ago for exactly this reason; CLAUDE.md was the one left behind.

The installer made the naive fix unsafe: it copies `CLAUDE.md.example` over the target and then `sed`s the target in place for personalization. Both operations follow a symlink, so a re-run would have written into the user's working copy of the repo, `test -f` being true for a symlink to a file.

## Predicted improvement

Divergence between the two copies becomes impossible rather than unlikely: they are one file. Any future change to CLAUDE.md reaches the running agent the moment it is saved, with no install step. Over the next 10 harness changes touching CLAUDE.md, zero require a manual re-copy.

## Invariants preserved

- `~/.claude/AGENTS.md -> CLAUDE.md` still resolves (relative link, now through the new symlink; verified: both paths return the same first line).
- Content is unchanged at the moment of the switch: `diff` between the installed copy and the repo copy was empty before replacing it.
- The installer keeps working unchanged for everyone who has a plain-file CLAUDE.md: the guards only fire on `-L`.
- The installer never writes into a developer's repo copy: neither the `cp` nor the personalization `sed` can reach it now.
- Backup of the pre-symlink file kept at `scratchpad/CLAUDE.md.pre-symlink.bak` (475 words).

## Falsification

If a session starts and its context does NOT include the CLAUDE.md content (Claude Code failing to follow the file symlink), the change broke the most important surface in the harness: restore the copy from backup immediately.

First check at the next session start: the instructions should appear sourced from `/Users/maroffo/Development/private/claude-forge/CLAUDE.md.example`, the same way `rules/*.md` already appear under their real repo paths through the `rules` directory symlink.

Second falsifier: if `install.sh` is re-run and `git status` in claude-forge shows a modified `CLAUDE.md.example`, a guard is missing somewhere: revert the symlink and reopen.

## Rollback

`rm ~/.claude/CLAUDE.md && cp <scratchpad>/CLAUDE.md.pre-symlink.bak ~/.claude/CLAUDE.md`, plus `git revert <commit>` for the two installer guards.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | verified live in this session, 2 days after merge | the primary falsifier is refuted directly, this session's context does include the CLAUDE.md content and ~/.claude/CLAUDE.md is a symlink to claude-forge/CLAUDE.md.example with ~/.claude/AGENTS.md still resolving through it; the second falsifier stayed negative, the main checkout shows no modification to CLAUDE.md.example, so no installer run has written through the link | kept |
