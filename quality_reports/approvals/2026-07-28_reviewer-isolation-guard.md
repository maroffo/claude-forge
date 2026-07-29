# ABOUTME: Redacted approval record for the reviewer-isolation-guard change (issue #116)
# ABOUTME: Counts and outcomes only; reproduction detail stays in the gitignored findings files

# Approval record: reviewer-isolation-guard (issue #116)

| Field | Value |
|-------|-------|
| Branch | `feat/reviewer-isolation-guard` |
| Commit approved | `c143d26` |
| Rounds run | 4 (highest artifact `004-findings.md`) |
| Findings path | `quality_reports/reviews/2026-07-28_reviewer-isolation-guard/` (local, gitignored) |

## Counts by severity, over the consolidated lists

| Round | Critical | Major | Minor | Agents |
|-------|----------|-------|-------|--------|
| 1 | 0 | 5 | 6 | security, architecture, test (3 launched, 3 completed) |
| 2 | 0 | 2 | 5 | security, test (2 launched, 2 completed) |
| 3 | 0 | 1 | 0 | security (1 launched, 1 completed) |
| 4 | 0 | 1 | 0 | security, test, each launched twice, all four truncated on an infrastructure stall |

All Critical: none, in any round. All Major and Minor findings are `fixed`, except one Minor
accepted (below). The round-4 Major is the truncation itself, resolved by the orchestrator
answering that round's questions directly with stronger evidence than the agents would have
produced (the resolver's own rejection message enumerates the entire agent universe).

## CWE ids

- CWE-117, improper output neutralisation for logs. Round 1, fixed.
- CWE-176 and CWE-180, improper handling of Unicode encoding and validate-before-canonicalise.
  Round 2, fixed.

## Final score

SCORE: 97/100 (threshold: 90, gate: pr)

100 minus one accepted Minor. Every other consolidated finding across four rounds is fixed and
re-verified.

## Residual risks, accepted

1. **The hook does not check that a brief carries the isolation assertion.** A launch that passes
   `isolation: "worktree"` but whose brief omits the assertion sentence yields a silently degraded
   read-only review. Adding a warn is new hook behaviour outside the approved plan and needs its own
   E2E row and contract. Plan decision 16, tech-debt row.
2. **`make check` does not shellcheck `hooks/*.sh`.** The new hook was linted by hand. Widening the
   Makefile glob would pull roughly 20 pre-existing scripts into this PR's gate. Plan decision 13,
   tech-debt row.
3. **Workflow-tool `agent()` launches are invisible to any PreToolUse matcher**, by construction.
   The agent-side write gate in the 7 reviewer definitions remains the covering layer. Plan
   decision 8, documented in the hook header and in `skills/orchestrator/SKILL.md`.
4. **The round-2 and round-3 test cases have had no independent tautology audit.** They were each
   mutation-verified by the orchestrator when written, but the reviewer pass that would have
   audited them is the one that truncated. Recorded in `004-findings.md`.
5. **Every claim about how the Agent tool resolves `subagent_type`** (case-insensitive, folds
   Unicode compatibility forms, folds separators, rejects rather than fuzzy-matches) was established
   empirically by launching agents and reading rejections and transcript attribution, not from
   published documentation. If the resolver changes, the matcher's completeness argument has to be
   re-run; `row_10_whole_roster` is the test that would catch a new reviewer, not a new fold.

## Follow-up filed

Issue #118, label `documentation`: `pr-review` Phase 4b expects reviewers to write red-green tests
in the throwaway clone, while the #115 agent-side gate downgrades clone-launched reviewers to
read-only. Pre-existing, not caused by this change.
