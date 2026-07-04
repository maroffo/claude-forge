# ABOUTME: Change contract for standardizing skill tool restriction on the allowed-tools frontmatter key
# ABOUTME: Failure mode = `tools:` is the subagent field and is silently ignored for skills; acp-namespaced entries break off-provider

# Harness Change Contract: allowed-tools standardization

Authored before landing. From the 2026-07-04 skill/hook audit (personal MODERATE-4, workflow MODERATE allowed-tools namespace).

## Component

Skill frontmatter (tool keys only, no description/body changes): `tools:` renamed to `allowed-tools: [...]` in cover-image, table-image, newsletter-digest, process-clippings, process-email-bookmarks, email-cleanup, inbox-triage, legacy-code-expert, mauro-blogger, blog-writer, cognitive-load-analyzer. acp-namespaced entries (`mcp__acp__Bash` etc.) replaced with plain tool names in gemini-review, source-control, cloud-infrastructure.

## Failure mode targeted

Declared tool scoping that does nothing: `tools:` is the subagent frontmatter field, ignored on skills, so e.g. cover-image's intended Bash+Read sandbox actually ran with full tool access. Separately, `mcp__acp__*` names only resolve under the acp provider, so those restrictions break the skill's own commands under plain Claude Code.

## Predicted improvement

Every skill that declares a tool restriction actually gets it. Immediately checkable: `grep -rn "^tools:" skills/*/SKILL.md` returns nothing; no `mcp__acp__` entries remain outside genuinely acp-specific skills (none).

## Invariants preserved

- Tool SETS unchanged: each skill allows exactly the tools it declared before, just via the effective key.
- clickup keeps `mcp__clickup__*` (a real MCP namespace, not acp).
- No description text touched (trigger surface unchanged).

## Falsification

If a skill starts failing because its declared set was always wrong and only worked via the ignored key (e.g. a skill that silently used Write while declaring Bash+Read), the declared set needs widening: fix the set, do not revert the key.

## Rollback

`git revert <commit>`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
