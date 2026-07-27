# ABOUTME: Change contract for the context-watcher PostToolUse hook + pause-signal rule line
# ABOUTME: Targets state loss when auto-compact fires mid-task with no prior save

# Harness Change Contract: context-watcher hook nudges state-save at 60/75/85% context

## Component

- `hooks/context-watcher.py` + `hooks/context-watcher.sh` (new, PostToolUse matcher `""`)
- `hooks/tests/test_context_watcher.py`
- `hooks/settings.example.json` + `~/.claude/settings.json` (registration)
- `rules/plan-first-workflow.md` Context Preservation: one paragraph making the nudge a mandatory pause signal

## Failure mode targeted

Auto-compact fires with no warning (observed by Max at ctx:100%, 2026-07-08 session) and nothing prompts saving resume state first, so the post-compact session restarts from a lossy summary instead of the living plan. Hooks receive no context-usage fields on stdin; the hook computes occupancy from the transcript tail (statusline formula: input + cache_creation + cache_read of the last assistant record) and injects one additionalContext nudge per band (60/75/85%).

## Predicted improvement

In sessions that cross 60% context, the living plan / `.continue-here.md` is updated between the first nudge and the compact in >80% of cases (checkable from trace + git timestamps). Qualitative: no more "what was I doing" re-exploration turns right after an auto-compact. Sample: next 10 long sessions.

## Invariants preserved

- Fail-open: hook exits 0 with no output on any error; a broken watcher never blocks tool use.
- At most 3 injections per climb (one per band); a post-compact drop below 60% rearms it. No per-tool-call spam.
- No behavior change below 60% context.
- Wrapper matches existing uv invocation pattern; no new dependencies.

## Falsification

If in the next 10 sessions the nudge fires repeatedly within the same band (marker logic broken, context spam), or a session shows the hook adding >2s latency per tool call, or nudges appear in short sessions that never approach compaction (window mis-sized), the change made things worse: revert.

## Rollback

`git revert <commit>`; remove the two `~/.claude/hooks/context-watcher.*` symlinks and the PostToolUse `""` block from `~/.claude/settings.json`. Affects: hooks/context-watcher.py, hooks/context-watcher.sh, hooks/tests/test_context_watcher.py, hooks/settings.example.json, rules/plan-first-workflow.md.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 24 session markers, 2026-07-08 to 2026-07-27 | band scheme superseded by 2026-07-10_context-watcher-window-aware.md, with the cutover visible on disk as values 60/75/85 through 2026-07-09 and 45/52/57 from 2026-07-10 on; the one-marker-per-session and one-nudge-per-band structure held throughout and no band-spam was observed | modified |
