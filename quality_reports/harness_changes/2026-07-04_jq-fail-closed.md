# ABOUTME: Change contract for failing closed when jq is missing in the two safety commit gates
# ABOUTME: Failure mode = missing jq made cmd empty, no match, gates silently disabled (fail-open)

# Harness Change Contract: jq fail-closed on safety gates

Authored before landing. From the 2026-07-04 skill/hook audit (MODERATE M1).

## Component

Hooks: `hooks/pre-commit-gate.sh`, `hooks/main-branch-guard.sh` (jq presence check before command extraction).

## Failure mode targeted

Without `jq` installed, `cmd` extraction yields empty, the trigger regex never matches, and the two safety-critical gates (pre-commit quality gate, main-branch guard) silently disable: the "model-proof" enforcement layer evaporates on any machine where jq is absent, with no signal to anyone.

## Predicted improvement

On a jq-less machine, the first `git commit` is denied with an actionable message (install jq) instead of sailing through ungated. Zero behavior change on machines with jq (all existing tests still pass).

## Invariants preserved

- Advisory hooks (gitignore-anchor-lint, routing) stay fail-open: only the two safety gates fail closed.
- No new dependency: the check uses `command -v`.
- The deny message names the missing binary and the fix.

## Falsification

If the deny ever fires on a machine that HAS jq (PATH quirk in the hook environment), the check is producing false lockouts: loosen to a warning or fix PATH handling.

## Rollback

`git revert <commit>` or delete the two `command -v jq` blocks.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
