# ABOUTME: Change contract for moving autoresearch-prompt model+pricing out of code into config
# ABOUTME: Failure mode = hardcoded model IDs/prices drift and require code+test edits to update

# Harness Change Contract: autoresearch-prompt model config-driven

Authored before landing. Linked from the commit body. Append-only after merge.

## Component

Skill: `skills/autoresearch-prompt/` (new `config.py` + `models.toml`; `evaluator.py`, `cli.py`, `SKILL.md`, tests updated).

## Failure mode targeted

Model ID (`DEFAULT_MODEL`) and per-model pricing were hardcoded in `evaluator.py`, with the model ID also baked into tests. Each model release made these stale, and updating them required editing production code AND tests (violating the repo's "fetch-don't-assume / no stale version pins" principle). A latent bug compounded it: the cost loop `break`ed on the first pricing entry, so cost ignored the model actually used.

## Predicted improvement

Updating the default model or a price becomes a one-line edit to `models.toml` (data), or a zero-edit `AUTORESEARCH_MODEL` env override, with no test changes. Cost figures become model-accurate (the break-on-first bug is fixed). Verifiable now: `grep -rn "claude-" skills/autoresearch-prompt/src --include=*.py` returns zero matches.

## Invariants preserved

- Full test suite passes (`uv run pytest`): was 54, now 64 (10 new tests for config + cost).
- `ruff check .` clean (line-length 99, py311). No mass-reformat of pre-existing files.
- CLI behavior unchanged for existing flags; `--model` still overrides; help shows the resolved default.
- Unknown model degrades gracefully to `(0.0, 0.0)` pricing, never raises.
- No new runtime dependency (stdlib `tomllib`).

## Falsification

If a future contributor reports the model/pricing is STILL hard to change (e.g. config not picked up at runtime, env override ignored), or if `compute_score` cost regresses to model-agnostic, the abstraction failed: revert to the inline constants.

## Rollback

`git revert <commit>` then delete `config.py` + `models.toml`. Affects: `skills/autoresearch-prompt/src/autoresearch_prompt/{config.py,models.toml,evaluator.py,cli.py}`, `skills/autoresearch-prompt/SKILL.md`, `skills/autoresearch-prompt/tests/{test_config.py,test_cli.py,test_evaluator.py}`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
