---
name: score
description: "Run the local quality gates (`make check` + `make test-e2e`) and report commit/PR/excellence readiness per `rules/quality-gates.md`. Use when user says /score, is this ready to commit, is this ready for a PR, or score my changes."
allowed-tools: [Bash, Read]
---

# ABOUTME: Quality gate scoring: runs make check + make test-e2e and grades against quality-gates
# ABOUTME: Reports commit-ready (>=80), PR-ready (>=90), excellence (>=95) with honest auto-fails

# /score

Compute a quick quality readiness signal for the current working tree.

## Process

1. Run `make check && make test-e2e`.
2. **Fail = 0**: if either target fails, score is 0 (auto-fail per quality-gates: tests/build broken is CRITICAL).
3. **Pass = 100 baseline**: if both pass, the static gate is green. For a full rubric-based score (Major/Minor deductions), invoke `/gemini-review` or `/advanced-review` and subtract:
   - 10 per Major finding
   - 3 per Minor finding
4. Report against the three thresholds from `rules/quality-gates.md`:
   - ≥80 commit-ready
   - ≥90 PR-ready
   - ≥95 excellence

## Output format

```
Score: <n>/100
Gate:  <commit-ready | PR-ready | excellence | BLOCKED>

Breakdown:
  make check:     <PASS|FAIL>
  make test-e2e:  <PASS|FAIL>
  Major findings: <n> (-<10n>)
  Minor findings: <n> (-<3n>)

Ready to commit:  <yes|no>
Ready to open PR: <yes|no>
Excellence:       <yes|no>
```

## Rules

- **Be honest.** If the output is ambiguous, report "inconclusive" and say why. Do not inflate.
- **CRITICAL trumps all.** A failing `make check`/`test-e2e` yields score 0 regardless of other factors.
- **Missing gate = not zero.** If `make check` or `make test-e2e` targets don't exist in the project, do NOT claim score 100. Report "gate missing, run `/project-checks` to scaffold" and refuse to score.
- **Review integration is optional.** If the user didn't ask for a full review, report the static gate result only and note that a rubric-based score requires a review agent pass.

## When to use

- Before `git commit`: quick readiness check.
- Before opening a PR: confirm ≥90 threshold.
- Mid-session checkpoint: answer "are we done?" with a number instead of vibes.

## When NOT to use

- Pre-commit already running as a hook: the hook gives a go/no-go; `/score` gives you a number and a breakdown. Different use.
- Large refactors where full review is warranted: go straight to `/advanced-review`, not `/score`.
