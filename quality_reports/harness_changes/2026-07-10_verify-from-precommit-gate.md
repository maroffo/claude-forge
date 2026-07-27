# ABOUTME: Change-contract for emitting VERIFY from git commits that pass the pre-commit-gate
# ABOUTME: Closes a trace blind spot where hook-run make check/test-e2e was invisible

# Harness Change Contract: VERIFY from pre-commit-gate commits

## Component

`skills/harness-trace/src/harness_trace/extractor.py`: a `git commit` tool call (not carrying a gate-bypass flag) now emits a `VERIFY` step, with `lint_clean` resolved from the commit outcome and `tests_pass` left unknown on success. Tests in `tests/test_extractor.py::TestVerifyFromPreCommitGate`.

## Failure mode targeted

VERIFY was only emitted when the session ran `make check`/tests as an explicit Bash tool call. The `pre-commit-gate` PreToolUse hook runs `make check` (and `make test-e2e`, unless the diff is docs-only) before every `git commit`, so sessions that verified only via committing looked unverified. Observed this session (2026-07-10): the security-reviewer and mail-writer commits passed the gate, yet the live trace showed zero VERIFY events, skewing `verification_strength.oracles_count` toward false zeros.

## Predicted improvement

Sessions that commit through the gate now carry at least one VERIFY with `lint_clean=True`. Across the next ~15 traced sessions, the share of committing sessions with `oracles_count == 0` drops from most toward near zero. `oracles_count` and the lint axis become truthful; `tests_pass` is deliberately NOT inferred from a commit (see invariants) to avoid fabricating a pass.

## Invariants preserved

Design is **fail-closed**, following the two review findings (arch + security, 2026-07-10):

- `tests_pass` is **never** set True from a commit. `make test-e2e` is skipped for docs-only diffs and the skip marker does not reach the commit's tool_result (verified empirically against this session's JSONL), so a landed commit cannot evidence tests. Only `lint_clean=True` is asserted (`make check` always runs).
- On `is_error`, a `"Pre-commit gate:"` reason, or a failure marker, resolution fails closed: set the named axis False, never True. A positive success line can never override the error signal (guards the spoofing case where failing-test output embeds `[hash] N files changed`).
- `git push` never emits VERIFY (only `git commit` does), and is checked before generic verify patterns so a commit message containing `pytest`/`make check` does not misroute.
- A bypassed commit (`--no-verify`/`--no-hooks`/`--no-pre-commit-hook`) emits no VERIFY (conservative; those flags are forbidden and do not actually skip the PreToolUse gate).
- A non-gate commit failure (e.g. "nothing to commit") names no axis: both stay `None`.
- Existing VERIFY paths (pytest, make check as direct Bash) unchanged; `VerifyData` schema unchanged.

## Falsification

If any trace shows a git-commit VERIFY with `tests_pass=True`, the change is wrong (it must never be inferred from a commit): revert. Also revert if a commit VERIFY shows `lint_clean=True` while the same session's raw JSONL holds a gate-failure deny for that commit. Concrete check over the next 10 sessions.

## Rollback

`git revert <commit>`. Single file of production code (`extractor.py`) plus its tests; both revert together.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 41 commit-shaped VERIFY events across 9 sessions, 2026-07-10 to 2026-07-27 | commits now emit VERIFY with lint_clean true and tests_pass left unknown, the exact fail-closed signature the contract specified, and every substantive post-contract session carries at least one (07-15 twice, 07-16, 07-25 twice, 07-27); the only post-contract session with oracles_count 0 is 2026-07-23, a single-event non-orchestrator session with no commits | kept |
