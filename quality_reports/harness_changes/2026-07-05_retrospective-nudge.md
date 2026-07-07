# ABOUTME: Change contract: /learning-docs nudge at deliberate context boundaries (manual compact, clear)
# ABOUTME: Replaces "always launch learning-docs on compact/clear" with a marker-gated context nudge

# Harness Change Contract: retrospective nudge

## Component

Hook: `hooks/retrospective-nudge.py` + `.sh` (new, dual-event). Registered: `PreCompact` (matcher `manual`, writes a marker; stdout is not injected there) and `SessionStart` (matcher `compact|clear`, prints the nudge) in live user settings and `hooks/settings.example.json`. Tests: `hooks/tests/test_retrospective_nudge.py` (6 cases).

## Failure mode targeted

Long-running sessions never reach the natural retrospective moment (session close), so /learning-docs runs only when someone remembers. The requested design ("always launch /learning-docs on compact and clear") was rejected deliberately: hooks cannot run an LLM skill, spawning a headless session per compact would bill a full run each time, and auto-compacts fire mid-task where a retrospective interrupt derails work. The nudge makes the reminder deterministic while leaving the decision to the model/human.

## Predicted improvement

A /learning-docs prompt appears in context at every deliberate boundary (manual /compact, /clear) and never at auto-compacts. Success: LEARNING.md updates start clustering at those boundaries over the next 10 long sessions (base rate today: retrospectives only via explicit invocation).

## Invariants preserved

- Auto-compact stays silent (marker only written on trigger=manual): no mid-task derailment.
- Marker is consumed on first nudge: no repeat nagging within a session.
- Fail-open, no output on any error; state confined to `~/.claude/tmp/retro-nudge-*`.
- Global scope is intentional (learning-docs applies to any project), unlike the forge-scoped checkpoint-reminder.

## Falsification

Nudge fires at an auto-compact or repeats within one session (gating broken), OR 10+ nudges pass with zero resulting /learning-docs runs (reminder ignored, dead weight): unregister and revert.

## Rollback

`git revert <commit>` and remove the two registration blocks from live settings.json; `rm ~/.claude/tmp/retro-nudge-*`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
