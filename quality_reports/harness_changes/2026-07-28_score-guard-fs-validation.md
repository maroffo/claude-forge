# ABOUTME: Change contract — score-evidence-guard validates the claimed evidence path on the filesystem
# ABOUTME: One failure mode: SCORE cites an evidence path that is missing, foreign, or older than the last edit

# Harness Change Contract: score-evidence-guard filesystem validation

## Component

Hook `hooks/score-evidence-guard.py` (Stop): first filesystem dependency of this hook. Adds, when the turn's SCORE line carries an `evidence:` path: resolve under the session's project dir, require the directory and its `metadata.json`, require metadata.json mtime >= the timestamp of the last source-edit transcript event. Also adds `evidence` to the `make` alternation of VERIFY_RE (here and in `verify-before-stop.py`, kept in sync) so `make evidence` counts as a verify command.

## Failure mode targeted

With the evidence field in the literal (contract 2026-07-28_score-evidence-path.md) but no validation, a session can fabricate credibility: cite a path that does not exist, points outside the repo, or predates the edits it claims to back. An unvalidated evidence claim is worse than none.

## Predicted improvement

In test scenarios (hooks/tests/test_score_evidence_guard.py): fabricated path blocks, stale bundle blocks, valid fresh bundle passes, bare legacy literal keeps the old behavior. Live: wasit pilot session with a fresh `make evidence` bundle ends the turn unblocked; the same claim after a post-bundle source edit is blocked.

## Invariants preserved

- Fail-open discipline: unexpected exceptions (unreadable/corrupt metadata, stat errors) exit 0; only a *present-but-provably-invalid* claim blocks. Infra errors never wedge a session.
- Stop-hook cost stays low: stat-only checks, no JSON parsing of the bundle, no directory walks.
- Absent evidence field = exact legacy behavior (two-confirmation gate unchanged).
- The legacy verify gate still applies even when the evidence path validates: the bundle complements, never replaces, the fresh-verify requirement.
- One nudge per turn; `stop_hook_active` short-circuit preserved.

## Falsification

A session is blocked despite a genuinely fresh, in-repo bundle (false positive rate observable in traces as blocks followed by immediate identical re-claims that pass); or hook latency on Stop grows noticeably (subjective session lag attributable to this hook); or a fabricated-path scenario from the test suite passes live.

## Rollback

Revert the evidence-validation branch in score-evidence-guard.py (the SCORE_RE evidence group can stay; it is covered by the other contract); remove `evidence` from the two VERIFY_RE alternations.

## Result

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
