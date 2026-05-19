# ABOUTME: When and how to write a harness change contract before modifying hooks, rules, skills
# ABOUTME: Implements paper §5.2.3 (harness mutations need predictions, invariants, falsification)

# Harness Changes

The claude-forge harness IS the runtime that operates Claude. Edits to it change the future distribution of agent behavior, often in ways the editor did not predict. Therefore: any non-trivial change to the harness substrate must be preceded by a **change contract** that states what we expect, what we promise not to break, and how we will know if we were wrong.

This rule formalizes §5.2.3 of arxiv 2605.18747 ("Code as Agent Harness"): "every proposed edit should carry a change contract: which component is modified, which failure mode it targets, what improvement it predicts, which invariants it must preserve, which evaluation can falsify it, and how it can be rolled back".

## When required (🔴)

A change contract is REQUIRED for:
- Adding or modifying a hook in `hooks/` (changes deterministic behavior of every future session).
- Adding or modifying a rule in `rules/` (changes the orchestrator protocol or quality gates).
- Modifying the `Permissions`, `Hooks`, or `Env` blocks of `settings.json` / `settings.local.json`.
- Creating a new skill in `skills/` OR materially changing an existing skill's `SKILL.md` description (which controls when it auto-triggers).
- Adding or modifying an agent definition in `agents/`.

## When optional (🟡)

Recommended but not required for:
- Typo fixes, link updates, ABOUTME tweaks.
- Internal refactors of a skill that do not change the SKILL.md or its auto-trigger surface.
- Test additions that exercise existing behavior.

## When skipped (🟢)

Skip entirely for:
- Application-side code (anything outside `hooks/`, `rules/`, `agents/`, `skills/`, `settings*.json`).
- Documentation-only changes in `README.md`, `LEARNING.md`, `blog/`, etc.

## Process

1. **Before editing**, copy `quality_reports/harness_changes/TEMPLATE.md` to `quality_reports/harness_changes/YYYY-MM-DD_<short-slug>.md` and fill in the six fields.
2. **Commit the contract together with the change** (same commit or its immediate predecessor). Reference the contract path in the commit body.
3. **After 10–20 sessions** (or whatever sample size the contract states), append a Result row. If the falsification condition fired, revert.
4. **Do not edit the contract retroactively.** If the prediction was wrong, write a new contract that supersedes; keep the audit trail.

## Why this is not optional

Without a contract, a harness edit looks identical to ordinary code. Reviewers cannot tell whether `s/3 retries/5 retries/` was a vibes-based tweak or a measured response. Six months later, no one remembers which class of failure the retry change was supposed to prevent, and the next editor undoes it for a different vibe-based reason. The contract is the difference between drift and engineering.

## Pointers

- Template: `quality_reports/harness_changes/TEMPLATE.md`
- Existing contracts: `quality_reports/harness_changes/`
- Inspiration: arxiv 2605.18747 §3.5.3 (Governed Harness Mutation), §5.2.3 (Self-Evolving Harnesses without Regression)
