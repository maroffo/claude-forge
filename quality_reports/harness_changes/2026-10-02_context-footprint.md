# ABOUTME: Change contract: cut session-start context from content no session in use needs
# ABOUTME: One failure mode: half of the startup context was argent (unused) and instructions loaded twice

# Harness Change Contract: startup context footprint

## Component

Repo (this PR):
- `install.sh`: stops creating `~/.claude/AGENTS.md -> CLAUDE.md`; removes that exact symlink when an earlier install left it, never a file the user wrote.
- `README.md`: architecture tree no longer lists the symlink.
- `MEMORY.md`: the `[LEARN:compat]` line that justified the symlink is marked superseded.

Machine-local, applied by hand on 2026-10-02 (not in git; listed so the rollback is complete):
- `~/.claude/AGENTS.md` symlink deleted.
- argent removed from the Claude Code global config: user-scope MCP server (`~/.claude.json`), `rules/argent.md`, the 18 `skills/argent-*` links, `~/.claude/agents/argent-environment-inspector.md`. The `argent` binary stays on PATH; `~/.agents/skills/argent-*` untouched.
- `~/.claude/settings.json`: `claudeMdExcludes` = the forge root `AGENTS.md` (kept for other tools, duplicates CLAUDE.md plus rules for Claude Code); `skillOverrides` turns off the claude.ai-synced `anthropic-skills:humanizer` and `anthropic-skills:skill-creator` (duplicates of forge `humanizer` and `skill-forge`); `frontend-design@claude-code-plugins` disabled (the `claude-plugins-official` copy stays).
- `linear-server` user-scope MCP removed (never authenticated).

## Failure mode targeted

The context loaded before the first message was 49.1k tokens (`claude -p "/context"` in the forge, 2026-10-02), and about half of it served no session in use:
- argent: ~13k of loaded tool schemas, 6.2k of `rules/argent.md`, ~2.2k of skill descriptions, 237 of agent description. Max uses argent in no repo today.
- Claude Code now reads `AGENTS.md` files as well as `CLAUDE.md`: `~/.claude/AGENTS.md` (a symlink to CLAUDE.md, 1.3k) loaded the global instructions twice, and the forge root `AGENTS.md` (1.6k) restated CLAUDE.md plus rules in forge sessions. No other tool reads `~/.claude/AGENTS.md` (Codex has `~/.codex/AGENTS.md`, Gemini `~/.gemini/GEMINI.md`, pi has no global file).

Found while answering Max's 2026-10-02 question "possiamo ottimizzare quello che viene caricato nel contesto?".

## Predicted improvement

`claude -p "/context"` in the forge reports at most 26k tokens at session start (trial with the same settings passed via `--settings`: 25k). Memory files drop from 20k to about 10.8k; MCP tools loaded from 15k to under 1k.

## Invariants preserved

- `~/.claude/CLAUDE.md`, every file in `rules/` and the auto-memory index still appear under Memory files in `/context`.
- Forge `humanizer` and `skill-forge` stay listed; only the synced duplicates are hidden.
- `install.sh` never deletes an `AGENTS.md` that is a regular file or points anywhere other than `CLAUDE.md`. (The old `ln -sf` overwrote a user-written file: verified in a scratch HOME, now fixed.)
- argent can be re-enabled per repo with `argent init` inside it.

## Falsification

Within 10-20 sessions, any of these means revert or modify:
- A session start in the forge measures above 26k tokens with no new skill, rule or MCP server added.
- CLAUDE.md or a `rules/` file missing from `/context` Memory files (the exclude list matched more than intended).
- A mobile or Chromium task stalls because argent is missing and the session does not point to `argent init`.

## Rollback

`git revert <commit>`; recreate the symlink with `ln -s CLAUDE.md ~/.claude/AGENTS.md`; restore `~/.claude.json` and `~/.claude/settings.json` from the session backups (or delete the `claudeMdExcludes`/`skillOverrides` keys and set the plugin back to true); re-run `argent init -y` from `~` for the global argent install; `claude mcp add` linear-server.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
