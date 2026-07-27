# ABOUTME: Tech debt discovered during planned work but not addressed, one line each
# ABOUTME: Each entry points back to the plan that surfaced it (rules/plan-first-workflow.md, Living Plans)

# Tech Debt

- 2026-07-27: the Review Artifacts gitignore guard is prose, not enforcement; a PreToolUse hook (or a test-e2e case) gating writes under `quality_reports/reviews/` on a target-repo ignore line would make it deterministic. From `plans/active/2026-07-27_swarm-forge-borrowings.md` (W2).
