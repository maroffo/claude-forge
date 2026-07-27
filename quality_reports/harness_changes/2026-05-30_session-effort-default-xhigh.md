# ABOUTME: Change contract for shipping effortLevel=xhigh in the settings fragment (Opus 4.8)
# ABOUTME: Failure mode = orchestrator under-reasons at the Claude Code default of high

# Harness Change Contract: session effortLevel default = xhigh

Authored before landing. Linked from the commit body. Append-only after merge.

## Component

Settings fragment: `hooks/settings.example.json` (new top-level `effortLevel` key + comment). Documented in `README.md` effort paragraph.

## Failure mode targeted

The shipped settings set no `effortLevel`, so installs run at the Claude Code default (`high`). Opus 4.8 recalibrated effort: `high` now allocates LESS thinking than on 4.7, and Anthropic documents `xhigh` as the recommended level for coding/agentic work. A contractor-mode coding harness left at `high` under-reasons on exactly the multi-step agentic tasks it exists to run.

## Predicted improvement

Higher first-pass plan/implementation quality on non-trivial (moderate/complex) tasks, fewer REVIEW->FIX rounds to reach the score threshold. Smallest sample: average `total_fix_rounds` over the next ~10 moderate/complex sessions vs prior baseline; expect a downward shift. (Effort is the lever; model is unchanged.)

## Invariants preserved

- `xhigh` is a documented, valid Claude Code effort level; `effortLevel` is a real settings key.
- The fragment stays a manual-merge example (install.sh does not auto-write user settings).
- Comment correctly states: drop to `high` if most sessions are light, omit the key for model default, do not assume 4.7 token costs.
- No model is force-pinned (model stays installer's choice; `opus` alias documented as the no-drift option).

## Falsification

If `xhigh` produces no measurable reduction in fix rounds over 10 sessions AND cost/latency per session rises noticeably (trace token totals up with flat quality), the default is not paying for itself: drop the shipped default to `high` and leave `/effort xhigh` as the manual opt-in.

## Rollback

`git revert <commit>`, or set `"effortLevel": "high"` (or remove the key). Affects: `hooks/settings.example.json`, `README.md` effort paragraph.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions (13 with orchestrator events) | insufficient data: the contract's metric is average total_fix_rounds over 10 moderate or complex sessions, and no FIX or fix-round event exists in any of the 20 traces, so neither the improvement nor the falsification could be measured; the setting is still shipped, and the 14 SCORE events (median 95, last five 100/84/94/100/100) are the only adjacent signal. Re-check once the extractor counts REVIEW to FIX rounds | kept |
