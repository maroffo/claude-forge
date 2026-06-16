# ABOUTME: Change contract for the gitignore-anchor-lint pre-commit advisory hook
# ABOUTME: Failure mode = bare-name .gitignore glob silently excludes tracked source (learning Pattern 4)

# Harness Change Contract: gitignore-anchor-lint hook

Authored before landing. Linked from the commit body. Append-only after merge. Implements Pattern 4 from `quality_reports/learning_corpus/recurrence-report.md`.

## Component

New hook: `hooks/gitignore-anchor-lint.py` + `hooks/gitignore-anchor-lint.sh`, registered in `hooks/settings.example.json` under PreToolUse / Bash with `if: Bash(git commit*)`.

## Failure mode targeted

A bare-name `.gitignore` entry (intended for a built binary, e.g. `golem` or `mirsad`) is a glob that matches a same-named directory at any depth (`cmd/golem/main.go`), silently excluding source that should be tracked. Recurred across 2 products / 3 occurrences in the corpus (golem `golem`, mirsad `mirsad`, mirsad `.env.*` eating `.env.example`), each costing a "where did my file go" debugging detour.

## Predicted improvement

Eliminate this class at commit time: the hook warns the moment a risky line is staged, before the file silently vanishes. Target: zero new bare-name-swallow incidents in repos where the hook is installed. Verifiable now: the hook's 5-case test matrix passes (bare name matching a tracked dir warns; `/`-anchored, `.env.*` with negation, `*.log`, and `node_modules/` stay silent).

## Invariants preserved

- Advisory only: emits `additionalContext`, never a deny. A commit is never blocked by this hook.
- Inspects only newly-added (`+`) lines in staged `.gitignore` files, not pre-existing patterns.
- Warns on a bare name only when it actually matches an existing tracked path segment (no warning on speculative or future names).
- Legitimate broad ignores (`*.log`, `node_modules/`, anything with a glob metachar or an embedded/leading slash) are untouched.
- No new dependency: stdlib only, run via `uv run --no-project`, same wrapper pattern as the other hooks.

## Falsification

Over 15 sessions, if the hook produces one or more false positives per session on intentional broad patterns (training MAx to ignore it), it is net negative: unregister it. Equivalently, if it never fires across many `.gitignore` edits that later turn out to have swallowed a file, the detection is too narrow and should be widened or dropped.

## Rollback

Unregister the `gitignore-anchor-lint.sh` line from `~/.claude/settings.json` (and `hooks/settings.example.json`), then `git rm hooks/gitignore-anchor-lint.{py,sh}`. `git revert <commit>` covers all three files.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
