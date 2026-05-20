# ABOUTME: When and how to write a harness change contract before modifying hooks, rules, skills
# ABOUTME: Implements paper §5.2.3 (harness mutations need predictions, invariants, falsification)

# Harness Changes

Any non-trivial edit to the harness substrate requires a six-field **change contract** committed alongside it. Source: arxiv 2605.18747 §5.2.3.

## Scope

| Level | Examples | Contract |
|-------|----------|----------|
| 🔴 Required | `hooks/`, `rules/`, `agents/`, settings.json `Permissions`/`Hooks`/`Env`, a skill's SKILL.md description (controls auto-trigger), creating a new skill | Yes |
| 🟡 Optional | Internal refactor of a skill that doesn't change trigger surface, test-only additions, ABOUTME tweaks | Recommended |
| 🟢 Skip | App-side code, `README.md`, `LEARNING.md`, `blog/`, `docs/` | No |

## The six fields

| Field | Content |
|-------|---------|
| Component | File(s) modified |
| Failure mode targeted | Specific observed or anticipated failure. One per contract |
| Predicted improvement | Numeric where possible, qualitative + sample size otherwise |
| Invariants preserved | Boundary conditions that, if broken, make this a regression |
| Falsification | Concrete observation that would prove the change made things worse |
| Rollback | How to undo, in one line |

## Process

1. Copy `quality_reports/harness_changes/TEMPLATE.md` to `YYYY-MM-DD_<slug>.md` and fill in.
2. Commit the contract together with the change. Reference the contract path in the commit body.
3. After 10-20 sessions, append a Result row. If falsification fired, revert.
4. Never edit the contract retroactively. Write a superseding contract instead.

## One change = one failure mode

Bundling multiple targets makes the Falsification field ambiguous. If you cannot phrase a single failure mode for the change, split it into two contracts.
