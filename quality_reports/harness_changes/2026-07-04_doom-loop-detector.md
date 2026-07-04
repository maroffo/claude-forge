# ABOUTME: Change contract for the doom-loop-detector PostToolUse hook (repeated edits to one file trigger a re-plan nudge)
# ABOUTME: Failure mode = iterating a failing approach on the same file instead of stopping to re-plan

# Harness Change Contract: doom-loop detector

Authored before landing. Linked from the commit body. Append-only after merge. Imports the LoopDetectionMiddleware pattern from LangChain's "Improving deep agents with harness engineering" and promotes the Problem-Solving rule ("Approach failing? Stop, re-plan. Don't push harder on a broken path") from prose to a mechanical signal.

## Component

New hook: `hooks/doom-loop-detector.py` + `hooks/doom-loop-detector.sh`, registered in `hooks/settings.example.json` under PostToolUse for Edit, Write, MultiEdit. Tests in `hooks/tests/test_doom_loop_detector.py` (runs via `make test-e2e`).

## Failure mode targeted

Repeated edits to the same file while chasing a failing fix: the model's bias under failure is "try harder on the same path", and nothing in the harness counts attempts. The prose rule and the second-opinion auto-trigger ("2+ failed root cause attempts") both depend on Claude noticing it is looping, which is exactly what fails during a doom loop.

## Predicted improvement

Sessions with 8+ edits to a single file where no re-plan or /second-opinion happened drop measurably. Verifiable via traces/transcripts over the next 20 sessions: after a nudge fires, the follow-up contains a strategy change (re-plan, error classification, /second-opinion) in the majority of true-loop cases.

## Invariants preserved

- Advisory only: emits `additionalContext`, never a deny, never blocks an edit.
- Silent below the threshold: first nudge at edit #5 to the same file, then every 3rd (8, 11, ...); legitimate incremental work sees at most an occasional one-liner, and the message explicitly says "if legitimate, carry on".
- Per-session state in user-owned `~/.claude/tmp` (same convention as routing-advisor, no shared-/tmp symlink surface), keyed by sanitized session id, capped at 200 tracked paths, written atomically (`os.replace`); corrupted, tampered, or missing state resets to empty, never crashes the hook. State files from sessions older than 7 days are garbage-collected on write.
- Blind spot, accepted: PostToolUse does not fire on failed tool calls, so a loop of erroring edits is not counted; only successful edits feed the counter.
- Stdlib only, `uv run --no-project`, same wrapper pattern as the other hooks.
- No interference with the other PostToolUse hooks (appended after routing-advisor in each matcher).

## Falsification

Over 15 sessions: if the nudge fires mostly on legitimate incremental work (e.g. long single-file refactors) and never coincides with an actual stuck loop, it is noise training Claude and Max to ignore hook context: unregister. Threshold: more than 80% of firings judged false-positive on transcript review, or zero behavior change after any true-positive firing.

## Rollback

Unregister the three `doom-loop-detector.sh` lines from `~/.claude/settings.json` (and `hooks/settings.example.json`), then `git revert <commit>`. Affects: hooks/doom-loop-detector.py, hooks/doom-loop-detector.sh, hooks/tests/test_doom_loop_detector.py, hooks/settings.example.json.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
