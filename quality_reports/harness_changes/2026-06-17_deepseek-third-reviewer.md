# ABOUTME: Change-contract for adding DeepSeek (via pi) as a third isolated second-opinion reviewer
# ABOUTME: Six fields from arxiv 2605.18747 §5.2.3 (treat harness edits like safety-critical code)

# Harness Change Contract: add isolated DeepSeek reviewer to second-opinion

Filename convention: `quality_reports/harness_changes/YYYY-MM-DD_<short-slug>.md`. Authored before the change lands. Linked from the commit body. Append-only after merge.

## Component

Skill `skills/second-opinion/` (SKILL.md description controls auto-trigger) plus new Docker image `docker/isolated-deepseek/` (Dockerfile + isolated-deepseek-review.sh) and the `docker/update-reviewer-images.sh` auto-update script.

## Failure mode targeted

Two-reviewer agreement (isolated Claude + isolated Gemini) can be false consensus: both are large Western frontier models with overlapping training distribution, so when they agree the user cannot distinguish "true" from "shared-architecture bias". A third opinion from a structurally different lab (DeepSeek, MoE, different training corpus) is needed as a tie-breaker and bias-breaker.

## Predicted improvement

On the next ~10 `/second-opinion` invocations, DeepSeek dissents from the Claude+Gemini consensus in at least 1 case where its objection is judged substantive (surfaces a risk/approach the other two missed). If it never dissents substantively across 10 runs, the third reviewer is pure cost and should be dropped.

## Invariants preserved

- All reviewers stay isolated: DeepSeek runs in Docker with no `~/.claude/` mount, project mounted `:ro`, `-t read` only (no edit/write/bash), `--no-session` (ephemeral).
- API key never touches host filesystem beyond the existing `~/.config/*-api-key` file convention; passed in-memory as `DEEPSEEK_API_KEY`.
- The prompt sent to DeepSeek is identical to the one sent to the other two reviewers.
- Adding the third reviewer does not block the skill when DeepSeek is unavailable: the other two still produce a usable synthesis.

## Falsification

If across the next 10 `/second-opinion` runs DeepSeek never produces a substantive dissent from the Claude+Gemini consensus (always echoes or adds nothing), revert: the added latency/cost/key-management is not justified. Also revert if the `-t read` isolation proves leaky (DeepSeek attempts or performs any write to the workspace).

## Rollback

`git revert <commit>`, then `docker rmi deepseek-reviewer:latest`. Affects: skills/second-opinion/SKILL.md, docker/isolated-deepseek/Dockerfile, docker/isolated-deepseek/isolated-deepseek-review.sh, docker/update-reviewer-images.sh.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
