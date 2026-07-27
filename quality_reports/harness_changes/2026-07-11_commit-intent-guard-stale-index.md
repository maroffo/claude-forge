# ABOUTME: Change contract: commit-intent-guard stub scan evaluates a stale index on index-mutating commit commands
# ABOUTME: Scan git diff HEAD (+ named untracked files) when the command chains an add or commits from the worktree

# Harness Change Contract: commit-intent-guard stale-index evaluation on index-mutating commands

## Component

Hook: `hooks/commit-intent-guard.py` — stub-scan and deletions-advisory diff source selection
(`scan_added_lines_for_stubs`, `staged_deletions`, new `INDEX_MUTATING_RE` + untracked-file scan),
plus regression cases in `hooks/tests/test_commit_gates.py`.

## Failure mode targeted

The hook is PreToolUse: it runs BEFORE the Bash command executes, but its stub scan reads
`git diff --cached` — the index as it is NOW. When the command itself mutates the index
(`git add X && git commit ...`, `git commit -a/-am/--all/--include`, `git commit <pathspec>`),
the hook judges the wrong content. Two directions, one root cause:

1. **False deny** (observed 2026-07-11, hikma-mirsad PR #568 merge): a stub-looking line was
   already fixed in the working tree; the chained `git add` would have staged the fix, but the
   hook denied on the pre-add index — and the deny also prevented the add, a perfect loop until
   the commands were split.
2. **Silent bypass** (anticipated from the same analysis): with a clean index, a chained
   `git add stub.go && git commit` (or `commit -a` on a tracked file, or an untracked new file)
   passes the scan and then stages + commits the stub the scan never saw.

## Predicted improvement

Over the next 20 sessions: 0 stale-index false denies on compound `add && commit` (1 observed
2026-07-11), and 0 stub commits landing via the compound/`-a`/named-untracked routes (the new
regression tests encode both directions). Plain `git commit` on a pre-staged index is
byte-identical in behavior.

## Invariants preserved

- Plain `git commit` (no chained add, no worktree-pulling flags): scan source stays
  `git diff --cached`; an unstaged worktree stub NOT being committed does not deny (boundary
  encoded as a regression test).
- Conventional-message check, bypass-flag deny, TODO/FIXME/XXX/placeholder patterns untouched.
- The hook never mutates the repository (no `git add -N` simulation, read-only git calls only).
- Unborn branch (no HEAD yet): falls back to `--cached` instead of erroring.
- Ambiguity widens the scan, never narrows it (e.g. `-a` detection over-matching scans more
  content — the fail-safe direction).

## Falsification

Two counters, both checkable post-hoc:
1. If within 20 sessions a deny fires on a worktree/untracked stub that was genuinely NOT part
   of the commit (over-approximation of `git diff HEAD` or of the add-target matching) more
   than twice, the widening is too aggressive: restrict the scan to the add/commit pathspec or
   revert.
2. If a stub still lands via an index-mutating commit (e.g. a glob pathspec the token matcher
   does not expand, `git add 'src/**'`), the coverage claim is false: extend `_add_targets`
   glob handling or revert to a deny-compound-commands design.

Known residual (documented, not a falsifier): `git add <glob>` with quoting the token matcher
cannot expand may leave an untracked stub unscanned; tracked files remain covered by
`git diff HEAD` regardless.

## Rollback

`git revert <this commit>`. Affects: `hooks/commit-intent-guard.py`,
`hooks/tests/test_commit_gates.py`, this contract file.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions (13 with orchestrator events) plus 33 merged agent PRs, 2026-07-11 to 2026-07-27 | no stale-index false deny and no stub-landing report since merge; hook unmodified since its own commit a76cdb6, 6 index-mutating regression cases still present in hooks/tests/test_commit_gates.py; the deny channel is not in telemetry (PERMISSION_EVENT = 0 across the corpus) so this is absence-of-complaint, not a counted zero | kept |
