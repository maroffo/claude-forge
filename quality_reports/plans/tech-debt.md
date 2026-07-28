# ABOUTME: Tech debt discovered during planned work but not addressed, one line each
# ABOUTME: Each entry points back to the plan that surfaced it (rules/plan-first-workflow.md, Living Plans)

# Tech Debt

- 2026-07-27: the Review Artifacts gitignore guard is prose, not enforcement; a PreToolUse hook (or a test-e2e case) gating writes under `quality_reports/reviews/` on a target-repo ignore line would make it deterministic. From `plans/active/2026-07-27_swarm-forge-borrowings.md` (W2).
- 2026-07-27: the plan-template Depth column and COVERAGE footer are prompt-only devices; if they decay (falsification of the plan-depth contract: 2+ of the next 10 test-heavy plans ship without them), build a presence-check hook or test-e2e case. From `plans/active/2026-07-27_gstack-borrowings.md` (decision 7).
- 2026-07-27: gstack's scrape-to-skillify carries transferable patterns for a future skill-forge "codify" mode (stage/test/approve/atomic-rename lifecycle, bounded conversation walk-back, pure-parser/impure-driver split); deferred, coupled to gstack's $B browse daemon + bun. From `plans/active/2026-07-27_gstack-borrowings.md` (decision 13).
- 2026-07-27: forge-drift-check matches hook registration by filename substring only; settings.json matcher-format drift (right file registered under the wrong event or matcher) is a known gap. From `plans/active/2026-07-27_gstack-borrowings.md` (decision 10).
- 2026-07-28: the follow-up filing rubric (plan-forge W(last) + issue-loop step 3b) reuses issue-triage's four questions at file time, judged by the orchestrator on its own draft — a self-assessment, unlike triage's fresh-context pass. Max flagged it needs a deeper look soon: what evidence a follow-up must carry to earn `agent:ready` at filing, and whether a cheap independent check (triage re-pass on loop-filed issues, or a required repro/verification field) should gate it. Falsification data will come from contract 2026-07-28_followups-agent-ready.md.
