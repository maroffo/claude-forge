# ABOUTME: Change contract for moving personal/third-party skills out of the public repo (mauro-blogger)
# ABOUTME: Failure mode = private content (another person's blog voice and vault paths) shipped in a public repository

# Harness Change Contract: private-skills boundary

Authored before landing. Supersedes the "commit mauro-blogger into the repo" half of `2026-07-04_one-skill-tree.md` (the versioning goal stands; the location was wrong for a public repo).

## Component

Skill removal: `skills/mauro-blogger/` deleted from the public repo, now versioned in the private repo `~/Development/private/claude-private-skills` and symlinked into `skills/mauro-blogger` per machine (gitignored, same pattern as `advanced-review`). `skills/_INDEX.md` row annotated.

## Failure mode targeted

Personal and third-party content (Mauro Medda's blog voice, tone corpus, vault paths) published in a public repository: a privacy boundary violation independent of any technical breakage, and one that versioning-in-repo (the previous fix for it being unversioned) made worse.

## Predicted improvement

The public repo contains zero third-party personal content; the skill stays versioned (private repo) and live (symlink verified at `~/.claude/skills/mauro-blogger`). Checkable now: `git ls-files | grep mauro` is empty on main after merge.

## Invariants preserved

- Runtime unchanged: the skill registry still lists mauro-blogger with the same description.
- The one-skill-tree symlink model unchanged; this adds a second machine-local link beside advanced-review, both gitignored.
- The private repo has its own git history (versioning goal from the superseded contract preserved).

## Falsification

If the machine-local link breaks silently on a fresh machine (skill missing with no signal), the pattern needs an install-time check: add a doc-garden or install.sh warning for dangling `skills/*` symlinks.

## Rollback

Re-add the directory from the private repo and drop the gitignore line: `git revert <commit>` plus `cp -R ~/Development/private/claude-private-skills/mauro-blogger skills/`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
