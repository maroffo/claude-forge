# ABOUTME: Change contract: fix duplicate SessionStart key in settings.example.json + add a drift guard
# ABOUTME: Duplicate JSON key silently dropped the codemap-session registration on template apply

# Harness Change Contract: settings.example.json duplicate SessionStart key

## Component

Settings fragment (template): `hooks/settings.example.json` (the merge-me template consumed by `install.sh` and by hand on new machines). Plus a new drift guard: `hooks/tests/test_settings_example.py`.

## Failure mode targeted

`hooks/settings.example.json` declared the `SessionStart` event key twice (one block for `codemap-session.sh` at `startup|resume`, a second block for `checkpoint-reminder.sh` and `retrospective-nudge.sh`). JSON object semantics keep only the last occurrence of a duplicate key, so any consumer parsing the template (installer or a human merging it) silently loses the `codemap-session.sh` registration. Observed 2026-07-07 while wiring the harness on a second Mac: the codemap SessionStart hook would never fire from a clean template apply. No test validated the template, so nothing caught it.

## Predicted improvement

A fresh template apply registers all three `SessionStart` matchers (`startup|resume` → codemap-session, `` → checkpoint-reminder, `compact|clear` → retrospective-nudge) instead of two. `codemap-session.sh` registration goes from silently-dropped to present in 100% of template-based installs. Regression recurrence: the new guard fails the pre-commit gate (`make test-e2e`) on any future duplicate key or dangling hook reference, so the same drift class cannot reach main again.

## Invariants preserved

- All previously-intended hook registrations remain (no matcher removed; verified by enumerating the parsed template: 3 SessionStart matchers, 2 PreCompact, 2 Stop, 1 SessionEnd, plus PreToolUse/PostToolUse unchanged).
- Template stays valid JSON.
- No change to any live `~/.claude/settings.json`; installer copy model untouched (repo-side template only).
- The guard reads only the template and the `hooks/` directory listing; it adds no runtime dependency and runs under `uv run --no-project python3` like the other hook tests.

## Falsification

If the new guard `test_settings_example.py` flags a false positive on a template that is actually valid (no real duplicate key, all hooks present), or if a template-based install after this change registers zero or duplicated SessionStart hooks, revert. Checkable via `uv run --no-project python3 hooks/tests/test_settings_example.py` and by parsing the resulting settings.

## Rollback

`git revert <commit>`. Affects: `hooks/settings.example.json`, `hooks/tests/test_settings_example.py`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
