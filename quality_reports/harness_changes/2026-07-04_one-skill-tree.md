# ABOUTME: Change contract for reconciling the repo and deployed skill trees (single source of truth)
# ABOUTME: Failure mode = ~/.claude/skills is a drifting copy: unversioned skills, undeployed fixes, rotted values

# Harness Change Contract: one skill tree

Authored before landing. From the 2026-07-04 skill/hook audit (personal-skills SEVERE-1), verified: `~/.claude/skills` is a plain directory copy, `mauro-blogger` exists only there (unversioned), `linkedin-post`/`pr-review`/`autoresearch-prompt` exist only in the repo (never deployed), and the deployed `blog-writer` rotted to a vault folder (`max-blog/`) that does not exist (the repo's `maroffo-blog/` is the real one, verified on disk).

## Component

Repo side (this commit): `skills/mauro-blogger/` committed into the repo (was unversioned), `skills/_INDEX.md` updated to cover all skills including previously-unlisted ones. Runtime side (manual post-merge step for Max, NOT performed by this change): replace the `~/.claude/skills` copy with a symlink to the repo checkout per README Option 2.

## Failure mode targeted

Two skill trees with no sync mechanism drift in both directions: fixes landed in the repo never reach the runtime (linkedin-post, pr-review), skills authored live never reach version control (mauro-blogger, one `rm -rf` away from gone), and copied values rot against reality (deployed blog-writer pointing at a nonexistent vault folder while the repo copy is correct).

## Predicted improvement

After the post-merge symlink flip: zero divergence by construction; every audit fix in batches A-D goes live the moment its branch merges; mauro-blogger is versioned as of this commit regardless of the flip.

## Invariants preserved

- This commit changes only the repo; the live runtime is untouched until Max flips the symlink after merging (flipping mid-review would deploy unmerged branch state).
- `advanced-review` stays a symlink into its own repo (intentional, now documented in _INDEX.md).
- mauro-blogger content committed verbatim except one em-dash moved into a code span for the skills/ lint (the `— Mauro` sign-off is quoted content).
- The installer copy model (get.sh/install.sh) remains valid for OTHER users; the symlink is the contributor/owner mode README already documents.

## Falsification

If after the flip a repo-side experiment (unmerged branch checkout) breaks a live session because the runtime now tracks the working tree, the symlink model trades drift for instability: revert to copies plus a deploy script with a freshness check.

## Rollback

Repo: `git revert <commit>`. Runtime: `rm ~/.claude/skills && mv ~/.claude/skills.backup ~/.claude/skills`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
