# ABOUTME: Change-contract for making context-watcher window-aware and threshold-relative
# ABOUTME: Fixes nudges firing ~5x too early on 1M-context sessions

# Harness Change Contract: window-aware context-watcher

## Component

`hooks/context-watcher.py` (+ `hooks/tests/test_context_watcher.py`): the watcher now detects the real context window (1M unless `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`) instead of hardcoding 200K, and derives its nudge bands from the auto-compact threshold (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, default 92) instead of fixed 60/75/85.

## Failure mode targeted

On a 1M-context session the watcher assumed a 200K window, so its "60/75/85%" bands fired at ~120K/150K/175K tokens, which are only ~12/15/17% of the real window. The nudges arrived ~5x too early and their percentage bore no relation to when auto-compact actually fires, reading as "auto-compact is broken / never fires at 60%". Observed 2026-07-10: this session sat at 209,754 tokens (105% of the assumed 200K, 21% of the real 1M) with three nudges already emitted and auto-compact nowhere near.

## Predicted improvement

Nudge percentage tracks true occupancy, and the first nudge lands just below the compact threshold (`threshold - 15` points) rather than at a fraction of it. On Max's config (1M window, override 60) the first nudge moves from ~120K tokens to ~450K, and every nudge now precedes the ~600K compact point instead of trailing it by 480K. Bands stay a pre-warning wherever the threshold is set.

## Invariants preserved

- Fail-open: any error still exits 0 with no output.
- One nudge per band per climb; the per-session marker + post-compact rearm behavior is unchanged.
- Explicit overrides still win: `CONTEXT_WATCHER_WINDOW` / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` pin the window.
- Bands remain strictly below the compact threshold (offsets 15/8/3), so a nudge cannot fire at or after auto-compact.
- Large-trailing-record scan, statusline token formula, and marker semantics untouched.

## Falsification

Revert if a 1M session reaches auto-compact with NO prior nudge (bands set too high, or window over-detected). Concrete check: over the next 10 sessions, every `[compact-resume]` should be preceded in the same session by at least one `[context-watcher]` nudge. Also revert if a genuinely 200K session (1M disabled) gets no nudge before compacting, which would mean the 1M-default over-estimated its window.

## Rollback

`git revert <commit>`. Affects `hooks/context-watcher.py` and `hooks/tests/test_context_watcher.py`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 15 session markers, 2026-07-10 to 2026-07-27 | every post-change marker carries 45, 52 or 57, which is the compact threshold of 60 minus the contracted offsets 15/8/3, replacing the pre-change 60/75/85 values, and the top band sits 3 points below the threshold so nudges still precede compaction | kept |
