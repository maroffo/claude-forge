# ABOUTME: Change contract: global CLAUDE.md loses rules that contradict each other or the harness
# ABOUTME: One failure mode: two applicable global rules disagree, so one is ignored unpredictably

# Harness Change Contract: resolve contradictions in the global CLAUDE.md

## Component

`CLAUDE.md.example` (symlinked as `~/.claude/CLAUDE.md` and, through it, `~/.claude/AGENTS.md`: loaded in every session of every project). `README.md` line for `MEMORY.md`.

## Failure mode targeted

Global rules that contradict each other or the harness, so which one wins depends on the moment:
- "Describe approach first, wait for approval" (all changes) vs 🟢 "Auto" for typos and single functions.
- "> 3 files affected? Stop" vs `rules/plan-first-workflow.md` (multi-file = plan, no threshold), which also blocked purely mechanical multi-file edits.
- "ALWAYS sg" vs `skills/_AST_GREP.md` after the 2026-09-23 prompt-audit (sg as default for code, rg for text/comments/TODO).
- "feature → PR → dev → main" in repos that have no `dev` (claude-forge PRs target main: #119, #120).
- "All files: ABOUTME" vs `hooks/aboutme-enforcer.py` (new source files only, with exemptions) and vs "match existing style".
- "[LEARN:category] to MEMORY.md" (twice) vs the harness auto-memory, whose MEMORY.md is an index where content is forbidden; forge's MEMORY.md last got a LEARN entry on 2026-07-16, auto-memory since.

Also removed as Claude-Code duplicates (Max's decision: this file targets Claude Code only): the compaction line (harness prompt + plan-first Context Preservation) and the Plan Mode section (last line of `rules/response-shape.md`). Capitalized emphasis (NEVER, FORBIDDEN, ALWAYS) is replaced by the rule with its reason, same rationale as the skills prompt-audit; the hard constraints (hooks bypass, push, main, em dashes) keep their content.

## Predicted improvement

Qualitative, sample 10 sessions: no session stops to ask approval for a 🟢 change, no session splits or halts a mechanical multi-file edit on file count alone, no correction written as a `[LEARN]` line into an auto-memory index. Word count roughly unchanged (475 → 472): the removed lines are offset by the reasons added to the remaining ones; the change targets consistency, not size.

## Invariants preserved

- Hard constraints unchanged in substance: no hook bypass flags, no push unless asked, no work on main/master without authorization, no em dashes, `uv` for Python.
- 🟡/🔴 still require proposal/approval before work.
- Every removed line is carried by a rule file or the harness prompt, cited above; nothing Claude Code relies on disappears.

## Falsification

Within 10-20 sessions: a 🟡/🔴 change starts without a proposal (the approval rule got weaker than intended), or a push/main/hook-bypass happens that the old capitalized wording would have prevented, or plan mode answers become verbose (the Plan Mode section was load-bearing after all).

## Rollback

`git revert` the commit; `CLAUDE.md.example` and the README line return to their previous content.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
