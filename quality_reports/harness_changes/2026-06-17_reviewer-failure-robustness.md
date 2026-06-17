# ABOUTME: Change-contract for hardening isolated-reviewer invocation against failure/hang
# ABOUTME: Six fields from arxiv 2605.18747 §5.2.3 (treat harness edits like safety-critical code)

# Harness Change Contract: graceful degradation + optional timeout for isolated reviewers

Filename convention: `quality_reports/harness_changes/YYYY-MM-DD_<short-slug>.md`. Authored before the change lands. Linked from the commit body. Append-only after merge.

## Component

Skill `skills/second-opinion/SKILL.md` (Step 4 degradation instruction) plus the three reviewer scripts `docker/isolated-{reviewer,gemini,deepseek}/isolated-*-review.sh` (optional wall-clock guard on the review `docker run`).

## Failure mode targeted

A single reviewer failing or hanging is not handled robustly. Observed live during the `/second-opinion` run on 2026-06-17: the isolated Claude container returned `401` (expired OAuth in the volume) while Gemini and DeepSeek answered. The skill had no instruction to degrade to a partial synthesis, and the standalone `.sh` scripts have no wall-clock bound when run from a terminal (a non-responsive reviewer hangs forever).

## Predicted improvement

On the next ~10 `/second-opinion` runs where a reviewer fails, the synthesis completes from the surviving reviewers with the missing one explicitly flagged, in 10/10 cases (no aborts, no silent drops). Terminal invocations of any `.sh` script that hit a non-responsive reviewer terminate within `REVIEW_TIMEOUT` (default 300s) when `timeout`/`gtimeout` is installed.

## Invariants preserved

- The guard is best-effort: when neither `timeout` nor `gtimeout` exists, the prefix expands to empty and `docker run` executes exactly as before (verified: guard renders `[]`, scripts pass `bash -n` and a live PONG test).
- No change to isolation, key handling, or mount flags of any reviewer.
- The orchestrated `/second-opinion` flow remains bounded by the harness Bash-tool timeout regardless of the script guard.
- Identical prompt still sent to all reviewers.

## Falsification

If a `/second-opinion` run aborts entirely (no synthesis) because one reviewer failed, the degradation instruction is not working, revert that part. If the `${TIMEOUT_CMD:+...}` guard ever prefixes a non-empty value on a host lacking `timeout` (breaking `docker run`), revert the script guard.

## Rollback

`git revert <commit>`. Affects: skills/second-opinion/SKILL.md, docker/isolated-deepseek/isolated-deepseek-review.sh, docker/isolated-gemini/isolated-gemini-review.sh, docker/isolated-reviewer/isolated-review.sh.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
