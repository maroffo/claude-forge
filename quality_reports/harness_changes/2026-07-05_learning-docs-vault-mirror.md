# ABOUTME: Change contract: learning-docs mirrors each new lesson to the vault (<project> - Learnings)
# ABOUTME: Closes the lessons->vault gap so retrospectives feed blog discovery and knowledge-sync

# Harness Change Contract: learning-docs vault mirror

## Component

Skill: `skills/learning-docs/SKILL.md` (workflow step 6 + vault-privacy note covering all vault copies). Docs: `CLAUDE.md.example` and live `~/.claude/CLAUDE.md` Knowledge Capture table.

## Failure mode targeted

LEARNING.md lessons stay siloed per repo: solutions and session logs already mirror to the vault, lessons do not, so retrospectives never reach blog-writer topic discovery or knowledge-sync promotion, and there is no single browsable archive of learnings across projects. (A central learnings repo was considered and rejected: second source of truth, and work-repo war stories must not aggregate outside the work perimeter, the same constraint that gitignores learning-loop's corpus.)

## Predicted improvement

Every learning-docs run appends its new lessons to `<project> - Learnings` in the vault. Success: over the next 5 learning-docs runs, the vault notes exist and blog-writer discovery can cite lessons among candidate topics. Repo LEARNING.md stays the source of truth (git history per repo).

## Invariants preserved

- Repo-first: vault copy is a mirror, never the primary; obsidian CLI unavailable -> skip, no path fallback.
- Work-perimeter privacy: the new note generalizes the exclusion rule to ALL vault copies in the skill (lessons, solutions, skill candidates): no client names, internal hostnames/architecture, unreleased or NDA content.
- Trigger surface (frontmatter description) unchanged.
- learning-loop's ingest is untouched (still reads repo LEARNING.md files).

## Falsification

Vault notes drift from repo LEARNING.md in ways that mislead (stale/edited copies treated as truth), OR work-sensitive content appears in a vault Learnings note: revert the step and keep lessons repo-only.

## Rollback

`git revert <commit>`; delete or ignore the `<project> - Learnings` vault notes. Affects: skills/learning-docs/SKILL.md, CLAUDE.md.example, live ~/.claude/CLAUDE.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
