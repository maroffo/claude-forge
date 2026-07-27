# ABOUTME: Change contract for the installer guard that refuses to write through symlinked install paths
# ABOUTME: Targets the data loss a re-run of install.sh causes on a developer machine that symlinks ~/.claude into the repo

# Harness Change Contract: install.sh never writes through a symlinked install path

## Component

`install.sh`: a `keep_symlinked` guard applied at every copy site (skills, rules, agents, hooks), plus a summary line listing what was left alone.

## Failure mode targeted

A developer of the harness symlinks parts of `~/.claude/` back at their working copy so edits are live without reinstalling. `cp` and `rsync` follow symlinks, so re-running the installer writes THROUGH those links into the repo, and `cp -R` onto a symlinked entry fails outright, aborting the script under `set -euo pipefail`.

Reproduced on `origin/main` in a sandbox mirroring the live layout (`~/.claude/rules` and `~/.claude/skills` as directory symlinks, per-file symlinks under `hooks/`, per-directory symlinks under `agents/`). One run:

1. overwrote `repo/rules/verification-protocol.md`, destroying the uncommitted edit;
2. wrote ~100 new files into `repo/skills/` through the symlinked directory;
3. exited 1 at `cp -R agents/` with "Not a directory", leaving hooks uninstalled and personalization unapplied.

Found by `/pr-review` on #100, where the same mechanism had been fixed for `CLAUDE.md` alone.

## Predicted improvement

Re-running `install.sh` on a machine with any symlinked install path leaves every file in the target repo byte-identical and exits 0, instead of clobbering at least one file and aborting. Sample needed: one run, since the failure is deterministic rather than probabilistic.

## Invariants preserved

- A plain (non-symlink) install is unchanged: a fresh HOME still receives 6 rules, 13 agent entries, 29 hooks, 48 skills, with CLAUDE.md personalized. Verified.
- Re-running onto a plain install stays idempotent and exits 0. Verified.
- The installer never silently skips: every skipped path is named in the closing summary, so a user cannot mistake "left alone" for "updated".
- No new dependency and no change to the interactive prompts.
- `shellcheck install.sh` stays clean.

## Falsification

If a user reports that an install did NOT pick up a rule, agent, hook or skill they expected, and the closing summary did not name that path, the guard is skipping something it should have written: revert.

Second falsifier: if the summary routinely lists paths on a machine where the user did not deliberately create symlinks, the `-L` test is matching something else (an installer-created link, for instance) and the guard is misfiring: revert.

## Rollback

`git revert <commit>`. Affects: `install.sh` only.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 0 installer runs since merge, against a prediction needing exactly 1 | insufficient data: the precondition never occurred, install.sh has not been re-run on this symlinked machine since the guard landed, so the deterministic one-run test is still pending; the current state is consistent with no clobber, ~/.claude/rules and ~/.claude/skills are still directory symlinks into the repo, ~/.claude/CLAUDE.md is still a symlink, and the main checkout has no modified tracked files; re-check by running install.sh once and confirming exit 0 plus a byte-identical repo | kept |
| 2026-07-27 | 1 install.sh run on the symlinked machine (the deterministic test the row above was waiting for) | all categories selected, exit 0; claude-forge working tree byte-identical before and after (git status diff empty); skills, rules and CLAUDE.md still directory or file symlinks, hooks still per-file symlinks, agents still per-directory symlinks; only side effect a dated backup dir in ~/.claude, which is the installer's normal behavior | kept |
