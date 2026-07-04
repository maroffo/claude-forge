# ABOUTME: Change contract for honoring chained checkout -b / switch -c before git commit in main-branch-guard
# ABOUTME: Failure mode = the guard evaluates the pre-checkout branch and denies a legitimate branch-and-commit chain from main

# Harness Change Contract: main-branch-guard honors the checkout chain

Authored before landing. Failure mode observed live in this session: `git checkout -b chore/... && git commit ...` launched from main was denied, because PreToolUse runs before the checkout executes, so `rev-parse` still reported main.

## Component

Hook: `hooks/main-branch-guard.sh` (chain-target resolution before the branch check). Tests in `hooks/tests/test_commit_gates.py` (12 → 16 cases).

## Failure mode targeted

A single-command "create branch and commit" chain, the exact pattern the guard's own deny message recommends, is rejected when launched from main: the guard judges the current branch instead of the branch the commit will actually land on. This forces splitting into two Bash calls and teaches that the guard is wrong sometimes.

## Predicted improvement

`git checkout -b X && git commit` and `git switch -c X && git commit` from main pass; committing on main (plain, or chained INTO main) still denies. Verified now by 4 new regression cases, including the spoof case (branch name mentioned only inside the commit message does not bypass, because only the text before the first `git commit` is inspected).

## Invariants preserved

- Plain commits on main/master still denied (regression-tested).
- `git -C` and `cd` resolution unchanged.
- Spoof-resistant: heredoc/message content cannot fake a checkout (prefix-only scan).
- Fail-safe direction unchanged: when no chain target is found, behavior is identical to before.

## Falsification

If a denied-should-allow or allowed-should-deny case appears (e.g. a chain form the regex misses, like `git checkout -b "name with space"`), extend the regex with a test; if the prefix heuristic is ever spoofed in practice, revert to the strict pre-checkout behavior.

## Rollback

`git revert <commit>`. Affects: hooks/main-branch-guard.sh, hooks/tests/test_commit_gates.py.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
