# ABOUTME: Change contract for living ExecPlans in plan-first-workflow (repo-first, four living sections)
# ABOUTME: Failure mode = vault-first static plans are illegible to fresh sessions; progress/decision context lost between sessions

# Harness Change Contract: living ExecPlans, repo-first plan storage

Authored before landing. Linked from the commit body. Append-only after merge. Imports the ExecPlans pattern from the OpenAI Codex cookbook ("Using PLANS.md for multi-hour problem solving") and the "repository knowledge as system of record" lesson from OpenAI's harness-engineering post (2026-02-11).

## Component

Rule: `rules/plan-first-workflow.md` (Process step 3, new "Living Plans (ExecPlans)" section, Context Preservation). Consistency edits: `CLAUDE.md.example` (Knowledge Capture, Plans line), `README.md` (vault Plans line).

## Failure mode targeted

Plans are written once at approval time, stored vault-first, and never updated during execution. A fresh session working in the repo cannot see the plan (the vault is outside the repo and requires an explicit obsidian call the session has no reason to make), so multi-session tasks resume from chat-summary guesswork: decisions get re-debated, discoveries made mid-task are lost, and `.continue-here.md` (the only living artifact) is deleted after resume, destroying the trail. Observed shape: "Decisions Made (with WHY — prevents re-debating)" already exists in `.continue-here.md` precisely because plans were not carrying this weight.

## Predicted improvement

Over the next 5 planned multi-session tasks: zero decisions re-debated after being recorded (currently the `## Decisions` table only captures refinement-time decisions, not execution-time ones), and a fresh session resumes from the plan file alone without needing chat history or vault access. Plan staleness at close (plan contradicting what was actually built) drops to zero because the Progress and Surprises sections are updated during execution.

## Invariants preserved

- Approval flow unchanged: refinement → plan mode → save → approve → orchestrator.
- Annotation cycle and checkpoint markers unchanged.
- The `## Decisions` table format is unchanged (append-only, supersede-not-edit).
- Vault mirroring stays available for cross-project tracking; only the source of truth moves.
- Always-on token cost: `rules/plan-first-workflow.md` grows by fewer than 25 lines.
- `.continue-here.md` remains valid for unplanned/simple work.

## Falsification

Over the next 10 planned tasks: if in 3 or more the Progress section is never updated after plan approval (dead weight, same rot as the vault plans), or if `quality_reports/plans/active/` accumulates 3+ plans that finished without moving to `completed/`, the living format is overhead theater in this harness: revert the commit (both the living format and repo-first storage, since the latter exists to make the former visible).

## Rollback

`git revert <commit>`. Affects: `rules/plan-first-workflow.md`, `CLAUDE.md.example`, `README.md`.

---

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| 2026-07-27 | 9 plans over 3 weeks (6 completed with retrospectives, 3 stale in active/) | falsification limb 2 fired exactly at threshold: 3 plans with landed work sat in active/ with Outcomes "(open)", the oldest for 3 weeks; limb 1 never fired (Progress maintained in all 3) and 3 plans closed correctly in the last 5 days, so the failure is the close step being skipped, not the format. Max reviewed on 2026-07-27 and chose kept: the 3 stale plans were closed with retrospectives in the same pass. Re-check: if plans go stale again within the next 10, the close step needs enforcement (hook or STORE-step gate), not another reminder | kept |
