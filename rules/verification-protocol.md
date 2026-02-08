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

- Tests BEFORE code. Always.
- Every project: unit + integration + e2e
- Skip ONLY with: "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"
- After writing code: list what could break, suggest tests to cover it

## Bug Fix Process

1. Write test that reproduces bug
2. Confirm fails → fix → confirm passes
3. Check for regressions
