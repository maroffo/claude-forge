# ABOUTME: Change contract for SessionEnd hook that auto-extracts trace JSONL
# ABOUTME: First real use of the change-contract template

# Harness Change Contract: SessionEnd hook auto-extracts trace JSONL for claude-forge

## Component

- `hooks/session-end-trace.py` (new) + `hooks/session-end-trace.sh` (new wrapper).
- `~/.claude/settings.json`: new top-level `SessionEnd` hook entry pointing at `/Users/maroffo/.claude/hooks/session-end-trace.sh`.
- `install.sh`: no change. Existing `cp hooks/*.{sh,py}` already covers the new files.

## Failure mode targeted

Zero trace JSONL files exist under `quality_reports/traces/` despite the `harness-trace` skill having existed since 2026-03-31. Cause: the skill is invoked manually only, and nobody invokes it. 10 raw sessions exist in `~/.claude/projects/-Users-maroffo-Development-private-claude-forge/` from the last 40+ days, none extracted. Without trace data, `harness-mechanic` cannot diagnose anything, so the whole telemetry-driven optimization loop (paper §3.5.1) is dead in the water.

## Predicted improvement

- `quality_reports/traces/*.jsonl` count grows from 0 to roughly 1 per session ended in claude-forge, automatically.
- Over the next 4 weeks (estimated 15-25 sessions on claude-forge), accumulate enough trace history to run `harness-mechanic` for real.
- Zero added user friction: the hook fires on `/exit`, Ctrl-C, and window close without prompting.

## Invariants preserved

- The hook MUST be a no-op when `cwd` is not the claude-forge repo. Other projects must see zero behavior change.
- The hook MUST NOT block session termination. Timeout 10s, fail-silent on any error.
- No secrets are read or written. The hook only touches `transcript_path` (read) and `quality_reports/traces/` (write).
- No `--no-verify` or similar bypass paths.
- `harness-trace` CLI contract unchanged: still callable manually.

## Falsification

- After 7 days from merge: if `ls quality_reports/traces/*.jsonl | wc -l` is still 0, the hook is not firing. Investigate (probably wrong `cwd` filter or missing executable bit). Revert if unfixable.
- After 14 days: if no trace file appears for a session that the user remembers running, the hook fires on some exits but not others. Either fix or revert.
- If a non-claude-forge session ever produces a file under `quality_reports/traces/`, the `cwd` filter is broken. Revert immediately.
- If session termination ever feels slower than before (user-reported), the hook is blocking. Revert.

## Rollback

Single `git revert` covers `hooks/session-end-trace.{py,sh}`. The settings.json entry is in `~/.claude/settings.json` (outside the repo): rollback there is manual, delete the `SessionEnd` block.

```bash
# Repo-side
git revert <commit>
# User-side
$EDITOR ~/.claude/settings.json   # remove "SessionEnd" entry
```

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|

Verdict: pending.
