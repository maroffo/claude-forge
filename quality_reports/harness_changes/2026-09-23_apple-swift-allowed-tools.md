# ABOUTME: Change contract: apple-swift allowed-tools switch from mcp__acp__* names to native tool names
# ABOUTME: One failure mode: the allowlist names tools that do not exist in Claude Code sessions

# Harness Change Contract: apple-swift allowed-tools use native tool names

## Component

Skill `skills/apple-swift/SKILL.md`, frontmatter `allowed-tools`: `[mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]` becomes `[Read, Edit, Write, Bash]`. Other hunks in the same batch commit are body-only.

## Failure mode targeted

The `mcp__acp__*` names come from an ACP bridge (Zed agent client) and match no tool in a native Claude Code session, so the pre-approval the field is meant to grant never applies there: every Read/Edit/Write/Bash while the skill is active falls back to the normal permission prompt. Anticipated from the 2026-09-23 prompt-audit; no session log of the prompts.

## Predicted improvement

In native Claude Code sessions with apple-swift loaded, Read/Edit/Write/Bash calls are covered by the skill's allowlist (no extra prompts attributable to the skill). Sample: 3 Swift sessions.

## Invariants preserved

- Scope does not widen past the four tools the skill already intended to allow.
- `permissions.deny` (`.git/hooks`, `~/.ssh`, credentials) still wins over the skill allowlist; no hook is bypassed.
- Frontmatter still parses (`make check`).

## Falsification

A session run through the ACP bridge (Zed) loses tool access or starts prompting where it did not before; or the skill fails to load in any client.

## Rollback

`git revert` the batch-1 commit on `chore/skills-prompt-audit`; or restore the `allowed-tools:` line in `skills/apple-swift/SKILL.md`.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
