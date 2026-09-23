# ABOUTME: Change contract: cognitive-load-analyzer description gains a "Use when" trigger clause
# ABOUTME: One failure mode: skill never auto-triggers because its description states what, not when

# Harness Change Contract: cognitive-load-analyzer description gets trigger conditions

## Component

Skill `skills/cognitive-load-analyzer/SKILL.md`, frontmatter `description` (controls auto-trigger). Other hunks in the same batch commit are body-only.

## Failure mode targeted

The description says what the skill computes (a 0-1000 CLI score over 8 dimensions) but has no "Use when" clause, unlike every other skill in the catalog. Requests such as "how hard is this codebase to understand", "complexity score before the refactor", "onboarding to this repo" carry no lexical overlap with "Cognitive Load Index", so the router has nothing to match. Anticipated from the 2026-09-23 prompt-audit.

## Predicted improvement

Skill-routing eval: cognitive-load-analyzer cases routed correctly stays at or above the main baseline; qualitatively, a request for a codebase complexity/understandability score loads the skill without naming it.

## Invariants preserved

- Does not steal routing from `project-analyzer` (CLAUDE.md generation), `architecture-reviewer` agent, or language skills' code review.
- "Architecture review" in the new clause must not route plain architecture-review requests here: routing eval confusions into cognitive-load-analyzer stay at 0.
- Description remains one YAML line, within `make check` limits.

## Falsification

Routing eval confusions show any case expecting project-analyzer, a reviewer, or `none` routed to cognitive-load-analyzer; or its correct-route count drops below the main baseline.

## Rollback

`git revert` the batch-4 commit on `chore/skills-prompt-audit`; or restore the old `description:` line in `skills/cognitive-load-analyzer/SKILL.md`.

## Result (filled in AFTER merge, append-only)

| Date | Sample size | Observed metric | Verdict |
|------|-------------|-----------------|---------|
| (after 10-20 sessions) | | | |
