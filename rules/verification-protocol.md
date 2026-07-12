# ABOUTME: TDD process — test before code, verify after every change
# ABOUTME: Mandatory test/lint/build cycle, no skipping without explicit authorization

# Verification Protocol

## TDD Process

1. Write failing test → confirm fails
2. Minimal code to pass → confirm passes
3. Refactor

## After Every Code Change

Run language-appropriate test + lint + build. Output MUST be pristine.

For changes touching rendered UI, tests are not enough: run the `verify-frontend` skill (real browser, console gate, before/after screenshots) before reporting the change done.

For hot-path tasks (a `.bench/baseline.txt` was captured at task start), run `make bench-compare` before declaring the change done; a significant regression is a Major finding to fix or explicitly accept, not a silent pass. See orchestrator-protocol.md (BENCH-BASELINE / VERIFY).

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

1. Write test/script that reproduces bug (orchestrator: REPRODUCE step 1b)
2. Confirm fails → fix → confirm passes (orchestrator: VERIFY checks `reproduction_confirmed`)
3. Check for regressions

When running under the orchestrator, reproduction is a traced step with two verified conditions: script fails before fix, script passes after fix. See orchestrator-protocol.md step 1b.
