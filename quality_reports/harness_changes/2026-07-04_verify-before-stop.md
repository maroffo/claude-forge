# ABOUTME: Change contract for the verify-before-stop Stop hook (edits without a subsequent test/check run block the turn end once)
# ABOUTME: Failure mode = turn ends declaring work done while source edits were never verified

# Harness Change Contract: verify-before-stop gate

Authored before landing. Linked from the commit body. Append-only after merge. Imports the PreCompletionChecklist pattern from LangChain's "Improving deep agents with harness engineering" (their single highest-impact harness change, +13.7 points on Terminal Bench 2.0 overall) and promotes `rules/verification-protocol.md` from prose to enforcement, per the forge philosophy ("text tells Claude what to do; hooks make sure it happens").

## Component

New hook: `hooks/verify-before-stop.py` + `hooks/verify-before-stop.sh`, registered in `hooks/settings.example.json` under Stop. Tests in `hooks/tests/test_verify_before_stop.py`, wired into `make test-e2e` (Makefile).

## Failure mode targeted

The turn ends with source files edited but no test/lint/build command run afterwards: verification-protocol says "run language-appropriate test + lint + build after every code change", but nothing enforces it, and the model's bias is to declare success after the edit looks right. The pre-commit gate only fires at `git commit`; work presented as "done" mid-session escapes it entirely.

## Predicted improvement

Turns that end with unverified source edits drop to near zero: the hook blocks the first stop and injects the remediation ("run the project's checks and report the outcome, or state explicitly why verification does not apply"). Measurable over the next 20 sessions via transcripts: count of turns where the hook fired and the follow-up contained a check run or an explicit justification.

## Invariants preserved

- Never blocks twice in a row: `stop_hook_active` guard makes it one nudge per turn.
- Docs-only turns (md, json, yaml, config) never trigger it.
- Scoped to the current turn (edits before the last human message do not re-trigger on later conversational turns).
- Sidechain (subagent) events and scratchpad/tmp paths are ignored.
- The hook never runs tests itself: it only redirects; a 15s timeout bounds transcript parsing.
- Stdlib only, `uv run --no-project`, same wrapper pattern as the other hooks.
- Escape hatch is honest reporting, not bypass: stating why verification does not apply is a valid exit.
- `git commit` counts as verification by design: the pre-commit-gate hook runs `make check && make test-e2e` on it, so commit-ending turns are already gated.
- Bounded work, deliberate fail-open: only the last 10MB of huge transcripts are scanned, lines over 1MB are skipped, commands truncated to 10k chars before regex. A timed-out or crashed hook must never block the stop.
- Sidechain lines (user AND assistant) are ignored for both edits and turn boundaries.

## Falsification

Over 15 sessions: if more than 30% of blocks are false positives (the turn's edits were already verified by a subagent, or the block fires on turns with no meaningful source change), the gate trains Max and Claude to ignore it: unregister. Also falsified if sessions routinely end via the escape hatch without ever running checks (the nudge produces justification theater instead of verification).

## Rollback

Unregister the Stop entry from `~/.claude/settings.json` (and `hooks/settings.example.json`), then `git revert <commit>`. Affects: hooks/verify-before-stop.py, hooks/verify-before-stop.sh, hooks/tests/test_verify_before_stop.py, hooks/settings.example.json, Makefile.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 20 traced sessions (13 with more than 3 events), 2026-06-08 to 2026-07-27 | evidence semantics in scan() and main() rewritten by 2026-07-05_verify-before-stop-failed-ids.md so a failed check no longer satisfies the gate, the hook remains registered on Stop alongside score-evidence-guard, and block counts are captured by no telemetry so the original near-zero-unverified-turns prediction stays unmeasured | modified |
