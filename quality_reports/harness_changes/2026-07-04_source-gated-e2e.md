# ABOUTME: Change contract for source-gating make test-e2e in the pre-commit gate (docs-only commits skip the suite)
# ABOUTME: Failure mode = full e2e suite runs on every commit including pure docs, dominating harness latency

# Harness Change Contract: source-gated test-e2e in pre-commit-gate

Authored before landing. From the 2026-07-04 skill/hook audit (SEVERE S2): the audit measured that hook process startup is negligible (~15-20ms warm) and the dominant enforcement-layer cost is the unconditional `make test-e2e` on every commit.

## Component

Hook: `hooks/pre-commit-gate.sh` (staged-diff gate before `make test-e2e`). Enabler: `scripts/check_repo.py` now also runs the skill-schema validation in `check` mode, so skipping e2e on markdown-only commits loses no SKILL.md validation in this repo. Plus a new `frontmatter first` lint in check mode (mechanically pins the bug class fixed in the frontmatter-registry contract).

## Failure mode targeted

Every commit pays the full `make check && make test-e2e` cost even when the staged diff is documentation or assets only. In repos with real e2e suites this is minutes per docs commit; it trains toward batching commits (worse bisectability) or resenting the gate.

## Predicted improvement

Docs-only commits drop from full-suite time to `make check` time. In claude-forge: a README commit stops running 7 hook test files. In application repos the saving is the entire e2e suite. Commits with any source file, `-a`/`--all`/`--include` flags, or an empty visible staging run everything, unchanged.

## Invariants preserved

- `make check` always runs: no commit lands with zero verification.
- Conservative bias: any non-docs extension in the staged diff, any stage-at-commit-time flag, or an empty staged list runs the full suite. Only a provably docs/assets-only staged diff skips e2e.
- SKILL.md schema validation still gates every commit (moved into check mode).
- The skip is announced on stderr, never silent.

## Falsification

If a regression ships through a docs-only-gated commit that `make test-e2e` would have caught (i.e. an e2e test that reads markdown/assets), the docs allowlist is wrong for that repo: revert or narrow the allowlist. Also falsified if the `-a` flag detection misses a stage-at-commit-time form in practice.

## Rollback

`git revert <commit>`. Affects: hooks/pre-commit-gate.sh, scripts/check_repo.py.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
