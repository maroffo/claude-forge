# ABOUTME: Change contract for fixing harness-mechanic AGENT.md frontmatter order and extending the lint to AGENT.md
# ABOUTME: Failure mode = ABOUTME above frontmatter made the harness-mechanic agent invisible to the Agent tool

# Harness Change Contract: AGENT.md frontmatter-first (harness-mechanic was unspawnable)

Authored before landing. Same failure class as `2026-07-04_frontmatter-registry-fix.md`, on a surface that fix missed: agent definitions.

## Component

Agent definition: `agents/harness-mechanic/AGENT.md` (ABOUTME moved below the frontmatter). Lint: `scripts/check_repo.py` `check_frontmatter_first` extended from SKILL.md to AGENT.md (red-green verified against a synthetic broken agent).

## Failure mode targeted

`harness-mechanic` was the only one of 12 agents absent from the Agent tool's registry: its AGENT.md opened with ABOUTME lines instead of frontmatter, so the definition never parsed. Consequence: the harness-mechanic SKILL could not spawn its own Evolution Agent, and the trace-driven optimization loop (session-end-trace → traces → harness-mechanic) was silently broken at the last step. Found because Max asked "does harness-mechanic actually work?": nothing mechanical was watching.

## Predicted improvement

harness-mechanic appears as a spawnable agent type from the next session (registry loads at session start; not verifiable in-session). The lint now fails ANY future SKILL.md or AGENT.md with content above the frontmatter, closing the class on both surfaces.

## Invariants preserved

- Description, effort (high), and body of the agent unchanged: only the block order moved.
- The 11 working agents untouched and still lint-clean.
- aboutme-enforcer still requires the 2 ABOUTME lines (they remain, below the frontmatter).

## Falsification

If harness-mechanic still does not appear in the next session's agent list, the frontmatter order was not the (only) cause: diff against a working AGENT.md field-by-field and re-diagnose.

## Rollback

`git revert <commit>`. Affects: agents/harness-mechanic/AGENT.md, scripts/check_repo.py.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
