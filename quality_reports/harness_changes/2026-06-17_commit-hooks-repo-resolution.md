# ABOUTME: Change contract for commit-gate hooks resolving the target repo from the command
# ABOUTME: Failure mode = hooks evaluate the session cwd repo, not the repo a cross-repo commit targets

# Harness Change Contract: commit-gate hooks repo-resolution

Authored before landing. Linked from the commit body. Append-only after merge.

## Component

New shared helper `hooks/_commit_target.sh` (sourced), plus the four commit-gate hooks that source it: `hooks/main-branch-guard.sh`, `hooks/pre-commit-gate.sh`, `hooks/commit-intent-guard.sh` (wrapper), `hooks/gitignore-anchor-lint.sh` (wrapper). The two Python logic files are unchanged; their wrappers `cd` before exec so the Python inherits the right cwd.

## Failure mode targeted

The commit-gate hooks run in the session cwd, which the harness resets to the primary working directory each call. When a commit targets a different repo via `cd <path> && git commit` or `git -C <path> commit`, every hook evaluated the wrong repo: `main-branch-guard` read the cwd repo's branch and falsely blocked a legitimate cross-repo commit whenever the cwd repo sat on `main` (observed twice in session 2026-06-16, cost a temp-branch workaround each time); `pre-commit-gate` ran the cwd repo's `make check` instead of the target's (a broken target commit could pass on an unrelated green build); `commit-intent-guard` and `gitignore-anchor-lint` scanned the cwd repo's staged diff, missing stubs/`.gitignore` issues in the actual commit. This is learning Pattern 1 (silent success) applied to the harness itself: the guard "passed" while guarding nothing.

## Predicted improvement

Cross-repo commits are evaluated in the repo they target. `main-branch-guard` false-block rate on legitimate cross-repo feature-branch commits drops to 0 (was 100% when cwd sat on main). The temp-branch-park workaround is no longer needed. Verifiable now: a 7-case end-to-end suite passes, including the exact bug (cross-repo commit on a feature branch is no longer denied) and the regression guard (a bare `git commit` while cwd is on main is still denied).

## Invariants preserved

- Resolution failure is never a regression: if the command gives no `cd`/`-C` hint, the helper echoes nothing and the hook keeps the current cwd (today's behavior). A bare `git commit` on a `main` cwd is still blocked (test C).
- A missing `_commit_target.sh` degrades gracefully: each hook guards the source with `[ -f ... ]` and falls back to cwd behavior.
- `main-branch-guard` still blocks commits whose resolved target is on `main`/`master` (test B). It never becomes more permissive: it evaluates the same repo the commit writes to.
- The Python hooks' logic is untouched; only their wrappers gained the resolve-and-cd preamble.
- `git -C` takes precedence over `cd` (that is where git actually operates).

## Falsification

If `main-branch-guard` ever ALLOWS a commit that lands on `main` (resolution points at the wrong repo and that repo is on a feature branch while the commit actually hits main), the resolver is unsafe: revert immediately. If a quoted/edge-case path makes a hook `cd` to an unintended directory and a gate runs against the wrong repo, revert. Watch the next cross-repo commits: if the temp-branch workaround is still needed, the fix did not take.

## Rollback

`git revert <commit>` then `rm hooks/_commit_target.sh`. Affects: `hooks/_commit_target.sh`, `hooks/main-branch-guard.sh`, `hooks/pre-commit-gate.sh`, `hooks/commit-intent-guard.sh`, `hooks/gitignore-anchor-lint.sh`. Re-run `install.sh` (CORE) or re-copy the hook scripts to `~/.claude/hooks/` to propagate the revert.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
