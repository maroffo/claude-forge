# ABOUTME: Change contract for running every review agent in its own worktree copy
# ABOUTME: Failure mode: a reviewer's writes landing in the main tree and being consumed by the next build

# Harness Change Contract: review agents run in an isolated worktree copy, not the main tree

## Component

- `skills/orchestrator/SKILL.md`, section Review Scheduling (launch carries `isolation: "worktree"`, base-SHA anchoring, cleanup order, honesty clause) and the Parallelism table's agent-class label.
- `rules/orchestrator-protocol.md`: step 3 REVIEW line and the "Review agents are read-only" invariant.
- The 7 review-agent definitions `agents/{architecture,database,dependency,dx,performance,security,test}-reviewer/AGENT.md`: the `## Rules` opening and the ABOUTME headers.
- `hooks/tests/test_agent_definitions.py` (new): pins the confinement line and the absence of a `tools:` key.

## Failure mode targeted

A review agent writes to the main tree and a later step consumes what it left. Concretely, from the PR #114 round (2026-07-28): the test-reviewer applied 11 mutants to a hook's source and ran the suite against each, and the security reviewer ran executable probes. Both restored the tree, but only because nothing crashed: a mutation run that dies between "apply mutant" and "restore" leaves corrupted source on disk, and the next build, the next test run and every concurrently running reviewer read it as the real thing. PR #114 widened this by scheduling reviewers concurrently with the writer, so a reviewer's leftovers now overlap in time with the implementation they are reviewing.

## Predicted improvement

Contamination incidents from reviewer writes go to zero by construction rather than by prose: the reviewer's filesystem root is a throwaway copy, so there is no write path to the main tree left to discipline. Sample: the next 10 review waves, checked by `git status` on the main tree before and after each wave (expected: no diff attributable to a reviewer, versus a current rate that is unmeasured but non-zero-by-luck, see above).

## Invariants preserved

- No `tools:` allowlist is introduced anywhere (rejected 2026-07-28 by two independent reviewers: theatre when `Bash` is allowed, capability-destroying when it is not). `hooks/tests/test_agent_definitions.py::test_no_tools_allowlist` fails if one reappears.
- Empirical review capability is preserved in full: mutation runs, executable probes and suite runs remain possible, now inside the copy. The finding that made PR #114 worth running would still be findable.
- No claim of prompt-injection prevention. This is isolation, not permission: a compromised reviewer can still write anything inside its own copy, and every document touched here says so.
- Findings stay checkable against the main tree: reviewer briefs name the base SHA and findings cite `file:line` against it, so the consolidation snapshot check still has an anchor.

## Falsification

Either of these says the change made things worse:

1. A reviewer finding anchored to a `file:line` that does not exist at the named base SHA, i.e. isolation broke anchoring and reviews now describe a tree nobody has. Checkable at consolidation with `git show <sha>:<file>`.
2. A main-tree `git status` diff during a review wave that is attributable to a reviewer, which would mean isolation is not actually being applied at launch (the parameter is documented, not enforced by any hook).

A third, softer signal: if worktree setup cost shows up as a measurable share of wave latency (budget: 200-500ms per agent, so above ~5s per wave something is wrong), the mechanism is not behaving as documented.

## Rollback

`git revert` the three commits of this change. Affects: `skills/orchestrator/SKILL.md`, `rules/orchestrator-protocol.md`, `agents/architecture-reviewer/AGENT.md`, `agents/database-reviewer/AGENT.md`, `agents/dependency-reviewer/AGENT.md`, `agents/dx-reviewer/AGENT.md`, `agents/performance-reviewer/AGENT.md`, `agents/security-reviewer/AGENT.md`, `agents/test-reviewer/AGENT.md`, `hooks/tests/test_agent_definitions.py`, this contract.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
