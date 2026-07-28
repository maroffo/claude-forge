# ABOUTME: Session log for the reviewer-isolation run (PR #115), vault CLI unavailable in this env
# ABOUTME: Fallback per rules/plan-first-workflow.md Session Logging

## 2026-07-28: reviewer worktree isolation (PR #115)
- Goal: isolation: "worktree" on every review-agent launch; read-only invariant restated honestly; test pinning the locked tools:-allowlist rejection.
- 3 review rounds (security+architecture, all worktree-isolated, agents=2/2), 3 fix passes, SCORE 97/100 gate pr. PR #115 open, not merged; follow-ups #116 (PreToolUse enforcement), #117 (citation-rule dedup).
- Key lesson: every defect (3 Major, 9 Minor) was an overclaim about the guarantee, never a broken mechanism: shared .git, guard testing worktree-ness instead of my-copy-ness, copy checkout at origin/main rather than the base SHA.
- E2E row 2 verified live three times: main-checkout git status byte-identical before/during/after every wave.
