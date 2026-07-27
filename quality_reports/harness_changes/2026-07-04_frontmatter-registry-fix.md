# ABOUTME: Change contract for fixing malformed SKILL.md frontmatter that broke registry descriptions/triggers
# ABOUTME: Failure mode = ABOUTME above frontmatter or missing description made skills advertise the wrong thing or nothing

# Harness Change Contract: SKILL.md frontmatter registry fix (6 skills)

Authored before landing. From the 2026-07-04 skill/hook audit (lang-skills SEVERE-1, workflow SEVERE-2, personal SEVERE-2). One failure mode: malformed frontmatter causes the skill registry to publish the wrong description (or none), so auto-triggering routes on the wrong text or not at all.

## Component

Skills (frontmatter/header blocks only, no body changes): `harness-trace`, `harness-mechanic`, `legacy-code-expert`, `cognitive-load-analyzer` (ABOUTME moved below the frontmatter), `autoresearch-prompt` (proper `description:` replacing non-standard `triggers:`/`version:` keys), `linkedin-post` (frontmatter added, previously none).

## Failure mode targeted

Four skills had `# ABOUTME:` lines above the YAML `---` block; the registry published the ABOUTME line as the description and discarded the authored trigger phrases (confirmed against the live session's skill list). autoresearch-prompt had no `description:` at all (unregistered, and newsletter-digest depends on it); linkedin-post had no frontmatter (inert).

## Predicted improvement

All six skills appear in the registry with their authored, keyword-rich descriptions; "use legacy-code-expert before verification-protocol on untested code" style auto-triggers become possible again. Verifiable immediately in the next session's skill list.

## Invariants preserved

- No description SEMANTICS changed for the four ABOUTME-order fixes: the authored text is untouched, only its position.
- ABOUTME headers preserved (aboutme-enforcer requires them for SKILL.md); now below the frontmatter per skill-forge's own template.
- autoresearch-prompt keeps its original trigger phrases, folded verbatim into the description.
- `make check` frontmatter lint and skill schema smoke still pass.

## Falsification

If any of the six skills starts auto-triggering on unrelated requests in the next 10 sessions (the restored descriptions are too broad), narrow that description with its own follow-up contract.

## Rollback

`git revert <commit>`. Affects the six SKILL.md files.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 6 skills, verified in the live session registry | all six skills now publish their authored keyword-rich descriptions rather than an ABOUTME line or nothing: harness-trace, harness-mechanic, legacy-code-expert, cognitive-load-analyzer, autoresearch-prompt and linkedin-post all appear in this session's skill listing with their trigger phrases intact, and none has been observed auto-triggering on unrelated requests | kept |
