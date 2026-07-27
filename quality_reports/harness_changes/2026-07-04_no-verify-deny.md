# ABOUTME: Change contract for denying hook-bypass flags (--no-verify & co.) in commit-intent-guard
# ABOUTME: Failure mode = flags declared FORBIDDEN in CLAUDE.md had zero mechanical enforcement

# Harness Change Contract: deny --no-verify / --no-hooks / --no-pre-commit-hook

Authored before landing. From the 2026-07-04 skill/hook audit (MODERATE M2).

## Component

Hook: `hooks/commit-intent-guard.py` (new check 0, before message validation). Tests in `hooks/tests/test_commit_gates.py`.

## Failure mode targeted

CLAUDE.md lists `--no-verify`, `--no-hooks`, `--no-pre-commit-hook` as FORBIDDEN, but no hook enforced it: under pressure (failing gate, long session) the model could bypass the entire enforcement layer with one flag, exactly the moment the rule exists for.

## Predicted improvement

Any commit command containing a bypass flag is denied with the rule's own rationale ("fix the failing hook systematically; pressure is not justification"). Verified now by 3 regression cases (one per flag, each with an otherwise-conventional message).

## Invariants preserved

- Implemented inside the existing commit-intent-guard process: no new hook, no added per-commit latency.
- Long flags only: `git commit -n` (short alias) is accepted as a known miss rather than risking false positives on `-n` inside message text.
- Commits without bypass flags see zero behavior change.

## Falsification

If the deny fires on a commit whose message merely MENTIONS the flag in quoted text (e.g. `-m "docs: explain --no-verify policy"`), the regex is too broad: anchor it outside quoted spans or scope it to pre-`-m` arguments.

## Rollback

`git revert <commit>` or delete check 0 in commit-intent-guard.py main().

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 3 weeks of commits, 0 bypass attempts | insufficient data: no commit in the corpus attempted a bypass flag and no commit message quoted one, so neither the deny nor its false-positive falsification had an occasion to fire; the three regression cases do run green in every test-e2e. Re-check the first time a session hits a red gate under pressure, which is the scenario the check exists for | kept |
