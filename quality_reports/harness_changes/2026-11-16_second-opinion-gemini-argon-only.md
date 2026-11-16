# ABOUTME: Change contract: second-opinion drops the dead Claude and DeepSeek reviewers, runs isolated Gemini on gemini-4-argon
# ABOUTME: Targets a three-reviewer panel that in practice answered with one flash model

# Harness Change Contract: second-opinion runs a single isolated Gemini on gemini-4-argon

## Component

`skills/second-opinion/SKILL.md` (description, compatibility, Step 4 calls, Step 5 synthesis), `skills/second-opinion/references/setup.md`. Blast radius: `skills/plan-forge/SKILL.md` ABOUTME and `skills/plan-forge/references/plan-template.md` Origin line (both said "3-lab"), `scripts/pr-watch/pr-watch.sh` prompt and env (no DeepSeek key), `scripts/pr-watch/README.md` and the root `README.md` skill table.

## Failure mode targeted

The panel the skill promises does not run. In the last 50 PRs reviewed by pr-watch (`~/.local/state/pr-watch/context.log`, one digest per PR, 2026-11-16), 45/50 report "DeepSeek 402" (balance exhausted) and 44/50 report no isolated-Claude image. The second opinion was one `gemini-3.6-flash` call presented as a cross-lab check, and the skill still spent tokens and time on two calls that could only fail.

## Predicted improvement

Over the next 20 pr-watch reviews that invoke `/second-opinion`: reviewer status OK in at least 18 (vs 0/50 full-panel runs now), zero "DeepSeek 402" or "isolated-Claude" strings in digests, and the reviewer model is `gemini-4-argon` in every status line.

## Invariants preserved

- The reviewer stays isolated: no `~/.claude` mount, project mounted `:ro`, key read in-memory.
- The failure procedure stays explicit: a failed call yields a status line and an open question, never a fabricated opinion and never a silent model substitution.
- The skill's trigger surface is unchanged apart from dropping "deepseek" from the user phrases (auto-trigger conditions identical).
- advanced-review keeps its own three-reviewer panel; this contract does not touch it.

## Falsification

Revert or modify if, over the next 20 invocations, more than 4 fail on `gemini-4-argon` (quota, 429, timeouts at 600 s), or if Max reports a second-opinion verdict that a cross-lab panel would have caught and Argon missed.

## Rollback

`git revert <commit>`. Affects: skills/second-opinion/SKILL.md, skills/second-opinion/references/setup.md, skills/plan-forge/SKILL.md, skills/plan-forge/references/plan-template.md, scripts/pr-watch/pr-watch.sh (prompt and DeepSeek export), scripts/pr-watch/README.md, README.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
