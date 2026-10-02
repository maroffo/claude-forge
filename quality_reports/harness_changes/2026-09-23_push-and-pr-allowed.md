# ABOUTME: Change contract: commit, push and PR opening become normal work; merging stays with Max
# ABOUTME: One failure mode: finished work stalls on a local branch waiting for a manual push

# Harness Change Contract: push and PR allowed, merge forbidden

## Component

`CLAUDE.md.example` (Git section) and `skills/source-control/SKILL.md` (Post-PR Loop push scope, Rules). Supersedes the push clause in the Falsification of `2026-09-23_claude-md-conflicts.md` ("a push ... that the old capitalized wording would have prevented"): pushing a feature branch is no longer a violation.

## Failure mode targeted

The old rule ("NEVER push automatically, Max pushes manually", with a /loop-only exception) left finished, verified work on a local branch until Max came back to push and open the PR by hand, and every session had to ask for a push authorization that Max always gave (2026-09-23: "committa pusha e apri una pr"). The real review gate is the merge, not the push: a pushed feature branch and an open PR change nothing shared.

## Predicted improvement

Sessions that finish a change end with a PR URL instead of a "branch ready, push when you like" hand-off; push-authorization questions drop to zero over 10 sessions.

## Invariants preserved

- No merge by the agent in any form: `gh pr merge`, auto-merge, local merge or push into the integration branch or main/master.
- Work on main/master still needs explicit authorization; pushes go to feature branches only.
- Force-push rules in source-control unchanged (`--force-with-lease` only, never bare `--force` on shared branches).
- Hooks never bypassed; pre-commit gate unchanged.
- Release tags (`releasing-software`) keep their own flow; this contract does not authorize tagging.

## Falsification

Within 10-20 sessions: any PR merged by the agent, any push to main/master or to the integration branch without authorization, or a PR opened on work that had not passed the repo's checks.

## Rollback

`git revert` the commit; `CLAUDE.md.example` and `skills/source-control/SKILL.md` return to the manual-push rule.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
