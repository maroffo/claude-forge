# ABOUTME: Change contract for closing the git -C bypass of all four commit gates
# ABOUTME: Failure mode = `git -C <path> commit` never matched the trigger regex, so every gate silently skipped

# Harness Change Contract: close the `git -C` commit-gate bypass

Authored before landing. From the 2026-07-04 skill/hook audit (SEVERE S1), verified by direct regex test (NO-MATCH).

## Component

Hooks: `hooks/pre-commit-gate.sh`, `hooks/main-branch-guard.sh` (shell trigger regex), `hooks/commit-intent-guard.py`, `hooks/gitignore-anchor-lint.py` (python trigger regex). Regression tests in `hooks/tests/test_commit_gates.py`.

## Failure mode targeted

`git -C /path commit ...` did not match `(^|[;&|\s])git\s+commit(\s|$)`, so all four commit gates exited 0 and the commit ran completely ungated (no make check/test-e2e, no main-branch guard, no intent checks). `_commit_target.sh` even contains `git -C` resolution logic that was dead code because the gates never fired for that form.

## Predicted improvement

Cross-repo commits via `git -C` are gated identically to plain commits, immediately. Verified now by the 12-case regression suite (deny on `-C` into a main-branch repo, deny on `-C` into a Makefile-less repo, message validation fires on `-C` form).

## Invariants preserved

- Plain `git commit`, `cd X && git commit` behavior unchanged (covered by tests).
- `git commit-tree` and `git log --grep commit` still ignored.
- Quoted `-C` paths containing spaces are accepted as a miss (documented in the pattern comment); unquoted and space-free quoted paths match.

## Falsification

If the widened regex fires on non-commit commands (false-positive gate runs on e.g. `git -C x log`) in any session, the pattern is wrong: revert. The regression suite pins the negative cases.

## Rollback

`git revert <commit>`. Affects the four gate files + the test file.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
