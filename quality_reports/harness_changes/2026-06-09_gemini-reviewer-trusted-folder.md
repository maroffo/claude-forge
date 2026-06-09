# ABOUTME: Change-contract for baking workspace-trust into the gemini-reviewer image
# ABOUTME: Six fields from arxiv 2605.18747 §5.2.3 (treat harness edits like safety-critical code)

# Harness Change Contract: trust the workspace in the isolated Gemini reviewer image

Filename convention: `quality_reports/harness_changes/YYYY-MM-DD_<short-slug>.md`. Authored before the change lands. Linked from the commit body. Append-only after merge.

## Component

skill infra: `docker/isolated-gemini/Dockerfile` (adds `ENV GEMINI_CLI_TRUST_WORKSPACE=true`), with redundant `-e` removed from `docker/isolated-gemini/isolated-gemini-review.sh` and a troubleshooting row added to `skills/second-opinion/SKILL.md`. Does not touch the skill's auto-trigger `description`.

## Failure mode targeted

Gemini CLI ≥0.45 refuses non-interactive runs in an "untrusted directory", aborting with `Gemini CLI is not running in a trusted directory`. The `docker run` invoked inline by the `second-opinion` skill (SKILL.md step 4) carried no trust flag, so the isolated Gemini reviewer failed on first headless launch. Observed 2026-06-09.

## Predicted improvement

`gemini_reviewer_trust_failures_per_invocation` drops from 1.0 (every headless run on CLI ≥0.45) to 0. Verified once at authoring time: inline `docker run` without the flag returns `TRUST_OK`.

## Invariants preserved

- Reviewer container still mounts project source **read-only** (`/workspace:ro`); trusting the workspace grants no write path.
- No API key reaches the host filesystem; key still passed via `-e GEMINI_API_KEY` in memory.
- Sandbox flag (`--sandbox false`) and stderr filtering unchanged.
- `second-opinion` auto-trigger surface (SKILL.md `description`) unchanged.

## Falsification

If a rebuilt `gemini-reviewer:latest` still emits `not running in a trusted directory` on a headless run, the ENV is not honored, revert. If the trusted workspace ever enables an unintended write (image gains a writable mount), the safety rationale is void, revert.

## Rollback

`git revert <commit>`. Affects: `docker/isolated-gemini/Dockerfile`, `docker/isolated-gemini/isolated-gemini-review.sh`, `skills/second-opinion/SKILL.md`. After revert, rebuild image: `docker/isolated-gemini/isolated-gemini-review.sh --build`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
