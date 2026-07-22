# ABOUTME: Change contract for the scripts/pi-exec executor wrapper + orchestrator executor-selection rule
# ABOUTME: Targets weekly Anthropic credit exhaustion; falsifiable over the first 5 pi-executed subtasks

# Harness Change Contract: route cost-sensitive implementation subtasks to pi + gemini-3.6-flash

## Component

- `scripts/pi-exec` (new executor wrapper, "other": script invoked by the orchestrator via Bash)
- `scripts/tests/test_pi_exec.py` (new offline test suite)
- `Makefile` (lint-shell + test-e2e wiring for the two files above)
- `rules/orchestrator-protocol.md` (new "Executor selection" subsection under Implementation, Step 1)

## Failure mode targeted

Weekly Anthropic credit exhaustion mid-week with backlog still open (observed 2026-07-22, planning session for this contract): implementation and mechanical-analysis subtasks burn Claude credits on work a cheaper, Google-billed model can do under the existing verification layer (review fleet, quality gates, hooks on the orchestrator's commits).

## Predicted improvement

Anthropic token spend per implemented issue drops 40-60% on tasks whose implementation subtasks route through pi-exec, measured via harness-trace using the literal `EXECUTOR:` report lines over the first 5 tasks.

## Invariants preserved

- SCORE thresholds and the quality-gates rubric unchanged.
- Review agents stay native (Fable/Opus) and read-only; review and spec roles are never routed to pi.
- The orchestrator is the sole committer; pi processes never commit.
- No `--no-verify` paths added.

## Falsification

Over the first 5 pi-executed subtasks: mean fix rounds > 2x the traced baseline, OR 2 or more subtasks require full re-implementation by the native software-engineer. Either observation: revert.

## Rollback

Stop invoking `scripts/pi-exec`; `git revert <commit>`. Affects: scripts/pi-exec, scripts/tests/test_pi_exec.py, Makefile, rules/orchestrator-protocol.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
