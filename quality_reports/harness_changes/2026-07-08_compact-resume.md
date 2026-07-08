# ABOUTME: Change contract for the compact-resume PreCompact/SessionStart hook pair
# ABOUTME: Targets re-planning from the lossy summary after an auto-compact instead of re-anchoring on files

# Harness Change Contract: compact-resume prompt after auto-compact

## Component

- `hooks/compact-resume.py` + `hooks/compact-resume.sh` (new; PreCompact matcher `auto` writes marker, SessionStart matcher `compact` prints the resume prompt)
- `hooks/tests/test_compact_resume.py`
- `hooks/settings.example.json` + `~/.claude/settings.json` (registration)

## Failure mode targeted

After an auto-compact the model continues from the lossy summary: it re-plans, re-explores, or drops in-progress tasks instead of re-reading the living plan / `.continue-here.md` that the rules already require. The compact summarization prompt is not customizable and PreCompact stdout is not injected, so the fix is a marker dance (mirroring retrospective-nudge) that injects, right after the compact, the concrete list of state files found in the cwd plus "trust files over summary, do not re-plan".

## Predicted improvement

Post-auto-compact turns start with a Read of the listed state files (or TaskList) instead of fresh exploration in >80% of observed auto-compacts over the next 10 sessions. Manual compacts stay untouched (retrospective-nudge owns that boundary).

## Invariants preserved

- Fail-open: exits 0 silently on any error.
- Silent on manual compact, /clear, startup, resume; exactly one message per auto-compact, marker consumed.
- retrospective-nudge behavior unchanged (separate marker namespace).
- No new dependencies; uv wrapper pattern.

## Falsification

If the resume prompt appears on manual compacts or /clear (boundary confusion), or if post-auto-compact sessions show the model re-reading large files it had already digested BECAUSE the prompt told it to (token cost per resume grows instead of shrinking), revert.

## Rollback

`git revert <commit>`; remove the two `~/.claude/hooks/compact-resume.*` symlinks and the PreCompact `auto` + SessionStart `compact` blocks from `~/.claude/settings.json`. Affects: hooks/compact-resume.py, hooks/compact-resume.sh, hooks/tests/test_compact_resume.py, hooks/settings.example.json.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
