# ABOUTME: Change contract: remove 11 skills with zero loads in two months of Claude Code transcripts
# ABOUTME: One failure mode: dead catalog entries cost context every session and crowd the router

# Harness Change Contract: remove unused skills (dormant tools, email and productivity)

## Component

Skills removed: `notion-sync`, `legacy-code-expert`, `swiftui-liquid-glass`, `cognitive-load-analyzer`, `table-image` (dormant tools); `mail-writer`, `clickup`, `bujo`, `bujo-sync`, plus the machine-local symlinks `email-cleanup` and `inbox-triage` (email and productivity; their content stays in `claude-private-skills`). Dangling references updated: `install.sh`, `README.md`, `skills/_INDEX.md`, `skills/_PATTERNS.md`, `skills/_generate_image.py`, `skills/skill-forge/SKILL.md`, the `description` of `skills/cover-image` and `skills/obsidian` (their "Not for... use <removed skill>" clauses), `.gitignore`, and the routing eval cases that expected a removed skill.

Supersedes `2026-09-23_cognitive-load-analyzer-description.md`: that description change is moot once the skill is gone.

## Failure mode targeted

Every session lists every skill description in context, and the router picks among all of them. Skills that are never loaded still pay that cost and add sibling candidates for real requests. Evidence: a scan of 873 Claude Code transcripts (2026-08 to 2026-09-23) for Skill tool calls, `<command-name>` slash invocations and "Base directory for this skill" markers found 0 loads for all 11 skills; none is referenced by a hook, rule or agent.

## Predicted improvement

Skill listing shrinks by 11 entries (about 20% of the 56-skill catalog). Skill-routing eval accuracy on the remaining cases stays at the pre-change level (31/31 minus removed cases, 37/37 minus removed cases, 8/8).

## Invariants preserved

- No hook, rule, agent or script loses a dependency (`make check` and `make test-e2e` stay green).
- `_GMAIL.md` stays: `newsletter-digest` and `process-email-bookmarks` still use it.
- `_generate_image.py` stays: `cover-image` still uses it.
- Requests that used to route to a removed skill route to `none` or a sensible sibling, never to a skill that acts on external systems (Gmail, ClickUp) without being asked.

## Falsification

Within the next 20 sessions, Max asks for one of the removed capabilities by name or by its trigger phrase (daily log, bujo, clickup task, rispondi a questa mail, cognitive load score, liquid glass, notion sync, table image), or the routing eval drops below the pre-change accuracy on the remaining cases.

## Rollback

`git revert` the two removal commits on `chore/skills-cleanup`; for the symlinks, `ln -s /Users/maroffo/Development/private/claude-private-skills/{email-cleanup,inbox-triage} skills/` and restore the two `.gitignore` lines.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
