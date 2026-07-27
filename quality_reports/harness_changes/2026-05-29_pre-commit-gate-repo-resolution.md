# ABOUTME: Change-contract for pre-commit-gate.sh repo resolution + no-Makefile skip
# ABOUTME: Fixes gate misfiring in multi-repo workspaces where the commit repo != harness cwd

# Harness Change Contract: pre-commit-gate resolves the commit's repo and skips repos without checks

## Component

hook `hooks/pre-commit-gate.sh` (PreToolUse on `git commit`).

## Failure mode targeted

In a multi-repo workspace, the harness Bash cwd is the seed repo (`hikma-onprem`), but commits target sibling repos via `cd <repo> && git commit` or `git -C <repo> commit`. The hook evaluated `Makefile`/`make check` in `$(pwd)` (the seed), not in the repo being committed. Result: every commit to a sibling repo was DENIED with "no Makefile in .../hikma-onprem", even when the target repo's checks were green. Observed repeatedly on 2026-05-29 (on-prem bundle work): wasit/frontend/mirsad agents all blocked from committing verified, green changes.

Scope note: the fix is repo-resolution ONLY. The no-Makefile branch still DENIES (the gate is not weakened); a repo that should be committable must add a Makefile with `check`/`test-e2e` targets (e.g. hikma-onprem got a Makefile that validates compose + shellchecks scripts). An earlier draft that turned no-Makefile into a silent skip was rejected as a gate weakening.

## Predicted improvement

Commits to sibling repos with green checks succeed without manual hook intervention: false-deny rate on `git commit` in the workspace drops from ~100% (every sibling-repo commit) to ~0% over the next 20 commits.

## Invariants preserved

- No `--no-verify` / bypass path is added; the gate still runs `make check` + `make test-e2e` when those targets exist in the resolved repo, and still DENIES on failure.
- A repo that HAS `make check`/`make test-e2e` is still gated exactly as before (red check still blocks).
- The gate still only fires on `git commit` (not `commit-tree`, not other git verbs).
- Resolution is read-only; the hook never mutates the repo or the index.

## Falsification

If a commit lands in a repo whose `make check` FAILS (i.e. the gate let a red check through), the change is broken — revert. Checkable: after the change, run a commit in a repo with a deliberately failing `make check` target and confirm it is still denied.

## Rollback

`git checkout <prev> -- hooks/pre-commit-gate.sh` (single-file change). No settings.json change.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | superseded after 19 days | repo resolution was generalized out of this hook into the shared helper hooks/_commit_target.sh by 2026-06-17_commit-hooks-repo-resolution.md, which pre-commit-gate.sh now sources; the trigger regex was widened again by 2026-07-04_commit-gate-git-c-bypass.md | modified |
