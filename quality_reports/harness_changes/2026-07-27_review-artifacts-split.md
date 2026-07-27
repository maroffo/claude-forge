# ABOUTME: Change contract for split-persistence review artifacts (gitignored per-round findings + committed redacted approval)
# ABOUTME: Source: 2026-07-27 swarm-forge borrowings analysis, second opinion by Gemini + DeepSeek (unanimous: findings carry exploit recipes, never commit them)

# Harness Change Contract: review rounds survive a compact, exploit detail stays local

## Component

`skills/orchestrator/SKILL.md` (new `## Review Artifacts` section: per-round `quality_reports/reviews/<YYYY-MM-DD_slug>/NNN-findings.md`, gitignore guard, committed `quality_reports/approvals/<YYYY-MM-DD_slug>.md`), `rules/orchestrator-protocol.md` (new `REVIEW-ARTIFACT:` literal report line, referenced from loop steps 3 and 8), `skills/pr-review/SKILL.md` (new Phase 0b: read the prior review record before judging).

Zero edits to `agents/`. The gitignore guard applies to target repos at loop runtime, not to claude-forge itself.

## Failure mode targeted

Review findings evaporate at auto-compact. They exist only in session context (`quality_reports/` holds traces, plans, session logs and harness contracts, no findings corpus), so fix round 3 cannot cite what round 1 reported, and the fix-round budget from `rules/plan-first-workflow.md` (default 5) is asserted in the final summary rather than auditable against anything.

## Predicted improvement

Qualitative, detectable on the first traced multi-round session: rounds become citable across a compact boundary because round N reads `001..N-1` from disk instead of from context, and the round count is auditable from the `NNN` sequence rather than from the summary's own claim. Second-order, one PR is enough to observe: `pr-review` stops re-litigating a finding the loop already recorded as `accepted`. Third-order and deliberately not wired now: `harness-mechanic` gains a corpus on review quality once one exists (smallest useful sample: roughly 10 sessions with review artifacts).

## Invariants preserved

- Per-round findings files never enter git history: the orchestrator ensures `quality_reports/reviews/` is gitignored in the target repo before the first write, appending the line, never rewriting the file.
- `approval.md` never carries exploit text, a reproducing command, or a vulnerable-code excerpt. CWE ids, counts, SCORE and residual-risk lines only.
- `NNN-findings.md` files are immutable once written: a later round writes the next `NNN` with `supersedes:` and fresh per-finding statuses, never edits an earlier file.
- Absence of `approval.md` means non-convergence, and is surfaced at PRESENT on the `REVIEW-ARTIFACT:` line (`converged=no`), never left for a human to notice.
- Review agents stay read-only: writing the artifacts is orchestrator work.

## Falsification

If a session writes an `approval.md` containing an exploit vector or a reproducing command, the redaction boundary failed and the change published exactly what it was built to keep local: revert.

## Rollback

`git revert <commit>`. Affects: `skills/orchestrator/SKILL.md`, `rules/orchestrator-protocol.md`, `skills/pr-review/SKILL.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
