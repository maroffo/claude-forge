# ABOUTME: Change contract for moving the email/LinkedIn skill cluster (personal PII) out of the public repo
# ABOUTME: Failure mode = personal email address, Gmail label IDs, and account config published in a public repository

# Harness Change Contract: private email/LinkedIn skills

Authored before landing. Second application of the private-skills boundary (`2026-07-04_private-skills-boundary.md`), extended from third-party content to Max's own PII.

## Component

Skill removals from the public repo: `email-cleanup`, `inbox-triage`, `newsletter-digest`, `process-email-bookmarks`, `linkedin-post`, plus the shared `_GMAIL.md`. All now versioned in the private `claude-private-skills` repo and symlinked machine-locally into `skills/` (gitignored). `skills/_INDEX.md` rows annotated.

## Failure mode targeted

Personal identifiers in a public repository: `maroffo@gmail.com` hardcoded in six skill surfaces, raw Gmail label IDs, personal newsletter subscriptions, and LinkedIn publishing configuration. Grep-verified list: every file matching `maroffo@gmail|aroffo@` under `skills/` outside the already-private ones.

## Predicted improvement

`grep -rn "maroffo@gmail" skills/` on public main returns nothing (only machine-local symlink targets contain it). Runtime unchanged: all six stay registered via the symlinks and keep their descriptions.

## Invariants preserved

- Same pattern as advanced-review/mauro-blogger: private git history + machine-local symlink + gitignore line; no new mechanism.
- Public skills that never contained PII (process-clippings, obsidian, bujo) stay public; their `_GMAIL.md` cross-references now resolve only on machines with the private link (documented in _INDEX.md).
- The private repo commit preserves full content including inbox-triage's src/ and tests.

## Falsification

Same as the boundary contract: a dangling `skills/*` symlink on a fresh machine with no signal means the pattern needs an install-time check. Additionally: if `make test-e2e` breaks because a public test reaches into a now-private skill, the split cut a dependency; move the dependent too or decouple.

## Rollback

`git revert <commit>` plus `cp -R` back from the private repo.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
