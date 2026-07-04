# ABOUTME: Phase 1 mechanics for pr-review: isolated clone, build gate, cleanup, troubleshooting.
# ABOUTME: Extracted from SKILL.md to keep the main file focused on the composing flow.

# Isolated Build Verification

Review always happens in a throwaway clone. Checking out the PR on the active repo would contaminate uncommitted work, staged changes, or an unrelated branch in progress.

```bash
# 1. Resolve the repo slug from the current working directory (PR is assumed to target the same repo)
REPO_SLUG="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

# 2. Fresh clone into a temp directory (full history: the commit narrative needs it)
PR_REVIEW_DIR="$(mktemp -d -t pr-review-<N>-XXXX)"
gh repo clone "$REPO_SLUG" "$PR_REVIEW_DIR"

# 3. Checkout the PR inside the clone (handles forks automatically)
git -C "$PR_REVIEW_DIR" fetch origin
(cd "$PR_REVIEW_DIR" && gh pr checkout <N>)

# 4. Run the project's build/test gate in the isolated clone
(cd "$PR_REVIEW_DIR" && make check)    # or equivalent from CLAUDE.md

# 5. Export the path for every subsequent phase
export PR_REVIEW_DIR
```

All subsequent phases (Gemini batches, delegated agents, source verification for Critical findings) MUST run with `$PR_REVIEW_DIR` as the working directory. The original repo is read-only from here on.

If the build fails, determine whether it is pre-existing or introduced by the PR: inside the clone, `git checkout <base> && make check`, then restore the PR branch afterward.

**Disk/time budget:** a full clone of a large repo can be slow. For repos > 1 GB or > 100k commits, use `gh repo clone "$REPO_SLUG" "$PR_REVIEW_DIR" -- --filter=blob:none` (partial clone: objects fetched on demand). Do NOT use `--depth N`: the commit narrative analysis needs the commit graph back to the PR's merge base.

# Troubleshooting

| Issue | Solution |
|-------|----------|
| PR too large for Gemini | Segment by package, < 3000 lines per segment |
| Agent returns hallucinated findings | Verify against source; check language version, DB engine |
| Build fails on base branch too | Note as pre-existing; still blocks merge |
| Too many findings to present | Group Minor as a count; focus the report on Critical + Major |
| Commit messages are useless ("fix", "wip") | Fall back to diff-only review; note poor commit hygiene |
| Clone fails (network, auth) | Review the diff only (`gh pr diff`); skip Phase 1 build verification and flag it as "unverified build" |
| Not enough disk for full clone | Re-run with `--filter=blob:none` (partial clone). Do NOT use `--depth`: commit history is needed for the narrative |
| `$PR_REVIEW_DIR` survives after abort | `rm -rf "$TMPDIR"/pr-review-*` is always safe; only temp clones live there |
