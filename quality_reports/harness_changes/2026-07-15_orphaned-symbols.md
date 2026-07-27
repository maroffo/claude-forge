# ABOUTME: Change contract for the orphaned-symbols rule: clean up what YOUR diff made unused
# ABOUTME: Producer rule in software-engineer + Minor deduction in quality-gates, pre-existing dead code stays protected

# Harness Change Contract: orphaned symbols left by a change are cleaned by the engineer and scored if they survive

## Component

Two files, one failure mode, two enforcement points:
- `agents/software-engineer/AGENT.md`, Implementation Rules: new rule 7 ("clean up your own orphans; pre-existing dead code is out of scope, mention it, don't delete it").
- `rules/quality-gates.md`, Scoring Rubric, Minor list: one new bullet for orphaned symbols (import/variable/function made unused by this same change and not removed).

## Failure mode targeted

Edits leave orphaned symbols behind: the diff removes the last caller of a function or the last use of an import/variable, nobody deletes the now-dead code, and the gate has no line to count it. Compiler/linter catches some cases (unused imports in Go, unused locals) but not exported functions, helpers in other files, or dynamic languages without strict lint. The existing harness states only the prohibitive half ("NO unrelated changes", R6 proportionality, conservation-of-complexity); the obligation to remove what YOUR change orphaned is unstated. Anticipated failure, imported from Karpathy's pitfalls ("don't clean up dead code", via multica-ai/andrej-karpathy-skills).

## Predicted improvement

Qualitative: over the next 15 sessions with multi-file diffs, 0 diffs land with orphaned symbols introduced by the diff itself (checkable in review: for each removed call site, a qualified grep of the callee shows remaining uses or removal). Smallest sample to detect: the first multi-file change that removes a call site.

## Invariants preserved

- Pre-existing dead code stays protected: R6 proportionality and the conservation-of-complexity gate (delete >20% / remove existing functions requires documentation + grep proof) are untouched and take precedence.
- "NO unrelated changes" unchanged: orphan cleanup applies ONLY to symbols made unused by the current diff.
- Orphaned symbol is Minor (-3), never Major or auto-fail.

## Falsification

If within the next 10 sessions an engineer deletes pre-existing dead code citing orphan cleanup (even once, verified via the Implementation Report or review finding), the wording is being misread as a license to prune: revert or reword with a superseding contract.

## Rollback

`git revert <commit>`. Affects: `agents/software-engineer/AGENT.md`, `rules/quality-gates.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 26 REVIEW events across 20 traced sessions, all with empty findings | insufficient data: per-finding data never reached telemetry, every REVIEW event carries "findings":{} and the 14 SCORE events carry only {score} with no deduction breakdown, so neither "0 diffs land with orphans" nor a Minor attributable to this bullet is computable; the falsifier (an engineer deleting pre-existing dead code citing orphan cleanup) has no reported occurrence; re-check once review-findings capture populates or by reading one review report by hand | kept |
