# ABOUTME: Plan for early-compact watcher + post-compact resume hooks
# ABOUTME: Fix ignored autocompact threshold, save state before compact, restart cleanly after

# Plan: Context-compact watcher + resume (2026-07-08)

## Goal

Auto-compact today fires at ~100% of the window despite `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` being set and active in the env. Max wants: (1) compact to effectively happen around 60% or at least never surprise mid-task, (2) higher precision across the boundary: state saved BEFORE compact, correct restart prompt AFTER compact.

Constraint discovered: the compact summarization prompt is not customizable (PreCompact hooks run around compaction, not inside; PreCompact stdout is not injected). So precision comes from state-on-disk + injected reminders, not from tuning the summary.

## Approach

Three components, three change contracts (one failure mode each):

1. **`hooks/context-watcher.py` + `.sh`** (PostToolUse, matcher ``): reads the tail of `transcript_path`, computes current context tokens from the last assistant `usage` (input + cache_read + cache_creation), and past a threshold (default 60%) emits a nudge to save resume state (living plan `## Progress` / `.continue-here.md`). Escalating thresholds (60/75/85) with a per-session marker file so it fires once per band, not per tool call. Fail-open. Injection channel: PostToolUse `hookSpecificOutput.additionalContext` (verify with docs; fallback UserPromptSubmit if unsupported).
2. **`hooks/compact-resume.py` + `.sh`**: PreCompact(auto) writes a session marker (stdout not injected there); SessionStart(compact) with marker prints the resume prompt: re-read `quality_reports/plans/active/*`, `.continue-here.md`, pending TaskList items, continue the interrupted task. Mirrors retrospective-nudge's marker pattern (which handles the manual-compact case and stays silent on auto).
3. **`rules/plan-first-workflow.md`** Context Preservation section: one line making the watcher nudge actionable ("when [context-watcher] fires, update the living plan / write .continue-here.md before continuing").

Plus diagnosis of the ignored `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (guide agent checking docs + GitHub issues); if a fix exists (e.g. explicit `CLAUDE_CODE_AUTO_COMPACT_WINDOW`), separate settings.json change + contract.

## Files

- `hooks/context-watcher.py`, `hooks/context-watcher.sh`, `hooks/tests/test_context_watcher.py`
- `hooks/compact-resume.py`, `hooks/compact-resume.sh`, `hooks/tests/test_compact_resume.py`
- `hooks/settings.example.json` (registrations)
- `~/.claude/settings.json` (registrations + possible env fix; symlinks `ln -s` post-merge per memory)
- `rules/plan-first-workflow.md` (one line)
- `quality_reports/harness_changes/2026-07-08_context-watcher.md`, `2026-07-08_compact-resume.md` (+ possibly `2026-07-08_autocompact-window.md`)

## Verification

- Unit tests per hook (payload → output), style of existing hooks/tests
- `make check && make test-e2e`
- Manual: feed synthetic transcript JSONL to context-watcher, assert nudge at ≥60% and silence below; assert marker dance for compact-resume

## Decisions

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| 1 | Compact timing | Keep auto-compact ON, watcher warns from 60% | Max: compact fires at 100%, override ignored; manual-only risks forgetting | Override bug gets fixed upstream |
| 2 | Precision levers | Post-compact resume hook + pre-compact save rule | Summary prompt not customizable; state-on-disk is the reliable channel | Claude Code adds custom compact prompts |
| 3 | Watcher data source | Transcript JSONL last assistant usage | Verified available (~72K tokens readable mid-session); independent of hook stdin schema | Hooks gain native context fields |

## Progress

- [x] 2026-07-08 Diagnosis: override env var present and active, compact still at 100% (Max's observation)
- [x] 2026-07-08 Verified transcript JSONL exposes usage tokens mid-session
- [x] 2026-07-08 Guide-agent: root cause is upstream bug (#52390/#63186, env block ignored); PostToolUse supports additionalContext; used_percentage = % of FULL window
- [x] 2026-07-08 context-watcher hook + tests (5 PASS)
- [x] 2026-07-08 compact-resume hook + tests (6 PASS)
- [x] 2026-07-08 settings registrations (example + live) + 4 symlinks in ~/.claude/hooks
- [x] 2026-07-08 shell workaround: export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=60 in workstation_setup zsh/.zshrc; settings.json env aligned to 60
- [x] 2026-07-08 rule line in plan-first-workflow.md Context Preservation
- [x] 2026-07-08 change contracts x3 (context-watcher, compact-resume, autocompact-shell-export)
- [x] 2026-07-08 make check && make test-e2e green; watcher fired LIVE in this session at 60%
- [x] 2026-07-08 architecture + security review: 0 CRITICAL; fixed TAIL_BYTES blind spot (growing backward scan, 16MB cap) + read cap + plan-name validation on injected filenames; accepted per-call polling cost (documented tradeoff, falsification bound in contract)
- [x] 2026-07-08 RE-VERIFY green (make check + test-e2e, 12 hook tests incl. new blind-spot case)
- [x] 2026-07-08 commit on feat/context-compact-watcher (Max pushes manually)

## Surprises & Discoveries

- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` has been set since 2026-05-19 and reaches the process env, yet compaction fires at ctx:100% (statusline). Either the var is ignored in 2.1.204 or the statusline denominator differs from the compaction window.
- PreCompact stdout is not injected into context (documented in retrospective-nudge.py); SessionStart stdout is.

## Outcomes & Retrospective

**Shipped:** context-watcher hook (PostToolUse, bands 60/75/85% from transcript-tail usage, additionalContext injection), compact-resume hook (PreCompact auto marker + SessionStart compact resume prompt listing real state files), pause-signal paragraph in plan-first-workflow, 3 change contracts, shell-export workaround for the ignored autocompact threshold (60%).

**Gaps:** (1) the 60% trigger at launch depends on the upstream bug workaround holding (contract falsification: first 5 auto-compacts); (2) compact-resume's real-world firing is untestable on demand, only unit-tested; (3) DEFAULT_WINDOW=200K is Max-specific, documented in settings.example but not auto-detected.

**Lessons:** the settings.json env block reaches subprocesses but NOT Claude Code's own logic (bug #52390/#63186): any env var meant to change app behavior must be exported by the launching shell. The watcher fired live at 60% during its own implementation session, which is the fastest harness-change validation loop we've had.
