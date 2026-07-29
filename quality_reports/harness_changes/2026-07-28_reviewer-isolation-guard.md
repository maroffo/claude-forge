# ABOUTME: Change contract for the PreToolUse hook denying un-isolated *-reviewer Agent launches
# ABOUTME: Failure mode: a write-encouraged reviewer launched into the real working tree because the isolation parameter was simply omitted

# Harness Change Contract: reviewer isolation is enforced at launch, not only documented

Follow-up to `2026-07-29_reviewer-worktree-isolation.md`, whose Falsification #2 named exactly this hole ("the parameter is documented, not enforced by any hook") and left it open.

## Component

- `hooks/reviewer-isolation-guard.sh` (new): PreToolUse hook on the `Agent` tool.
- `hooks/settings.example.json`: new `PreToolUse` block with `matcher: "Agent"`, timeout 10, registering the hook. Source of truth for the `~/.claude/settings.json` block Max applies after merge.
- `hooks/tests/test_reviewer_isolation_guard.py` (new): E2E rows 1 to 6, auto-picked by the `Makefile` `test-e2e` glob.
- Doc surfaces made true again in the same change: `skills/orchestrator/SKILL.md` (Review Scheduling, the fail-open bullet), `rules/orchestrator-protocol.md` (the read-only invariant clause), `skills/pr-review/SKILL.md` Phase 3 (reviewer briefs open with the exemption line), `README.md` hook inventory row.

## Failure mode targeted

A `*-reviewer` subagent launched through the `Agent` tool without `isolation: "worktree"`, i.e. a write-encouraged reviewer standing in the real working tree. #115 shipped both the launch parameter and the agent-side prose guard, but nothing inspected the launch itself: the parameter was an instruction to a launcher that could simply forget it, and the omission path is precisely the unattended one (a distracted or autonomous orchestrator does not notice what it did not type). The agent-side gate keys on an assertion the omitting launcher also omits, so on that path it downgrades the reviewer to read-only, which trades tree contamination for a silently degraded review. Neither outcome is observable at launch time. Observed as an open item, not yet as an incident: PR #114's review round had a test-reviewer apply 11 mutants to a hook's source in the main tree, before the parameter existed at all.

## Predicted improvement

- Un-isolated `*-reviewer` launches reaching execution on the `Agent` tool path: to 0 by construction, since the hook denies before the launch happens. This is a hard zero on that path only, and it is the only path a PreToolUse matcher can see: Workflow-tool `agent()` launches and an edited or unregistered hook stay prose-only, covered by the agent-side downgrade.
- Exemptions stay countable rather than silent: `grep -c '^ISOLATION-EXEMPT:' ` over session transcripts, expected steady state 1 per `pr-review` reviewer brief and 0 elsewhere.
- Sample needed: 10 sessions containing at least one review wave. A single observed deny with a relaunch that then passes (E2E row 7, the live dogfood) confirms the message loop; the rate claim needs the 10 sessions because omission is intermittent by nature.

## Invariants preserved

- Fail OPEN on every environment failure: missing `jq`, unparseable payload, absent `subagent_type`, a cwd outside any work tree. Only the policy violation itself denies. The gated action is corrigible (a launch, and writes that show up in the diff), while a false deny bricks every review in every session until someone notices. Pinned by E2E rows 5 and 6.
- The 7 `agents/*-reviewer/AGENT.md` files stay byte-identical: no PINNED churn, and the agent-side three-condition write gate remains the universal backstop for the launch paths this hook cannot see. Pinned by `hooks/tests/test_agent_definitions.py`, including its 7-file hash.
- `pr-review` keeps working: its throwaway-clone flow deliberately cannot pass `isolation: "worktree"`, and passes the guard via the line-anchored exemption instead of being denied.
- No `tools:` allowlist is introduced anywhere (locked in #115, decision 2, and not relitigated here).
- The exemption silences this hook for one launch and nothing else. It is not a write-enable: an exempted brief carries no isolation assertion, so the reviewer still self-downgrades to read-only agent-side. Stated at every place the marker is documented.

## Falsification

1. **Any deny of a launch that DID carry `isolation: "worktree"`**, or a deny caused by an environment condition (no `jq`, a payload the hook could not parse, a cwd outside a work tree) rather than by the policy. Either is a false positive on a fail-open hook, which is the one thing this design promised not to do. Checkable from the deny reason in the transcript against the launch payload; revert on the first occurrence.
2. **Exemption abuse:** more than 2 `ISOLATION-EXEMPT:` lines per session outside `pr-review`, measured over 10 sessions. That would mean the escape hatch has become the normal path and the hook is enforcing nothing, at which point the marker needs tightening or removal rather than the hook keeping the credit.

## Rollback

`git revert <commit>`, then remove `~/.claude/hooks/reviewer-isolation-guard.sh` (the installed symlink) and the `Agent` block from the `PreToolUse` array of `~/.claude/settings.json`. Affects: `hooks/reviewer-isolation-guard.sh`, `hooks/settings.example.json`, `hooks/tests/test_reviewer_isolation_guard.py`, `skills/orchestrator/SKILL.md`, `rules/orchestrator-protocol.md`, `skills/pr-review/SKILL.md`, `README.md`, this contract.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
