# ABOUTME: Change contract: trace extraction also fires on PreCompact, filenames keyed on session start date
# ABOUTME: Multi-day sessions that never reach SessionEnd stop losing their traces

# Harness Change Contract: PreCompact trace snapshot

## Component

Hook registration: `session-end-trace.sh` added to the `PreCompact` event (all triggers) in live user settings and `hooks/settings.example.json`; internal extraction timeout 8s -> 25s. Skill: `skills/harness-trace/src/harness_trace/cli.py` gains `trace_output_path()` keying the trace filename on the session's first-event date instead of the extraction date.

## Failure mode targeted

Sessions kept open for days accumulate work but only emit a trace at SessionEnd, which such sessions rarely reach (user reports routinely continuing for days without closing). Each auto or manual compact was a trace-less boundary. Secondary defect the fix exposed: extraction-date filenames would have turned each compact-day snapshot of one session into a separate trace file, double-counting sessions in checkpoint-reminder and harness-mechanic corpus stats.

## Predicted improvement

Every compact (manual or auto) leaves a current trace snapshot on disk; the later SessionEnd extraction overwrites the SAME file (verified by `trace_output_path` unit tests). Expected: trace corpus covers long-running sessions within one compact-interval of their latest state, instead of not at all.

## Invariants preserved

- One session = one trace file, regardless of how many times it is extracted.
- Hook stays scoped to claude-forge cwd (traces live in this repo) and fail-silent.
- `/clear` path unchanged: SessionEnd already fires with reason=clear.
- Baseline TSV naming untouched (extraction date is correct there: baselines are point-in-time measurements).

## Falsification

Two trace files appear for the same session slug with different date prefixes (naming regression), OR compaction latency visibly degrades because extraction runs in the PreCompact path (move to async/background then). Either over the next 10 sessions -> revert.

## Rollback

`git revert <commit>` and remove the PreCompact block from live settings.json. Affects: hooks/session-end-trace.py, hooks/settings.example.json, skills/harness-trace/src/harness_trace/cli.py, live user settings.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 trace files, 2026-06-08 to 2026-07-27 | 20 files carry 20 distinct session slugs so the naming-regression falsification never fired, and 5 files were written a day after their filename date (four 2026-07-04 traces written 07-05, one 07-25 trace written 07-26) which is the session-start-date keying holding across a day boundary | kept |
