# ABOUTME: TDD process — test before code, verify after every change
# ABOUTME: Mandatory test/lint/build cycle, no skipping without explicit authorization

# Verification Protocol

## TDD Process

1. Write failing test → confirm fails
2. Minimal code to pass → confirm passes
3. Refactor

## After Every Code Change

Run language-appropriate test + lint + build. Output MUST be pristine.

## Rules

- Every project: unit + integration + e2e
- Skip ONLY with: "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"
- After writing code: list what could break, suggest tests to cover it

## Outcome Verification

After tests/lint pass, produce a verification table for non-trivial changes:

| Observable Truth | Evidence | Pass/Fail |
|------------------|----------|-----------|

Truths = behaviors derived from the goal, not implementation details. Evidence = command output, file existence, observable result. "All tests pass" alone is insufficient: tests can encode the same wrong assumption as the code.

On failure: don't retry the same way. Classify the error (syntax, logic, design, environment) and adjust context/strategy accordingly.

## Bug Fix Process

1. Write test that reproduces bug
2. Confirm fails → fix → confirm passes
3. Check for regressions
