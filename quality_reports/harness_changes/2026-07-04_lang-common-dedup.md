# ABOUTME: Change contract for extracting the shared Version + Pre-Commit boilerplate from the 7 language skills
# ABOUTME: Failure mode = ~30 identical lines per language skill restate always-loaded rules, costing tokens every trigger

# Harness Change Contract: _LANG_COMMON.md dedup

Authored before landing. From the 2026-07-04 skill/hook audit (lang MODERATE-1/MINOR-1).

## Component

Skills: new shared `skills/_LANG_COMMON.md`; SKILL.md of golang, python, rails, ruby, react-nextjs, android-kotlin, apple-swift (boilerplate replaced with a pointer, per-language command lists kept inline). Staleness fixes riding along: ruby version pins genericized, apple-swift/ios-debugger simulator names parameterized, android-kotlin inlined code deduplicated against its own references.

## Failure mode targeted

Seven near-identical copies of the "Version (determine, don't assume)" and "Pre-Commit Verification" prose: every language-skill trigger pays ~30 lines that restate rules/verification-protocol.md (always loaded) and the pre-commit-gate hook (mechanical). Copies also drift independently, as the ruby version pins already had.

## Predicted improvement

Roughly 200 lines removed across the 7 skills (measured in the commit diff) with zero behavior loss; future edits to the shared prose happen in one file. Per-trigger token cost of each language skill drops accordingly.

## Invariants preserved

- Per-language check/test/lint command lists stay INLINE in each skill (the actionable part).
- No frontmatter description changes (trigger surface untouched).
- The pre-commit gate itself is unchanged; only prose about it is deduplicated.
- fetch-don't-assume semantics preserved verbatim in the shared file.

## Falsification

If a language skill consumer misses the version-check behavior because the pointer is not followed (observable as stale-version answers in the next 10 language-skill sessions), pointers are too weak for this content: re-inline a 2-line summary per skill.

## Rollback

`git revert <commit>`. Affects the 8 files above plus _LANG_COMMON.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 7 language skills, 3 weeks | the dedup holds structurally, with skills/_LANG_COMMON.md present and all 7 language skills pointing at it instead of carrying their own copy of the version and pre-commit boilerplate, and no stale-version answer recorded since; the corpus is thin on the falsification, since none of the 20 traced sessions is a language-skill-heavy session that would test whether the pointer is actually followed | kept |
