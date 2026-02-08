# ABOUTME: TDD process — test before code, verify after every change
# ABOUTME: Mandatory test/lint/build cycle, no skipping without explicit authorization

# Verification Protocol

## TDD Process

1. Write failing test
2. Confirm it fails
3. Write minimal code to pass
4. Confirm it passes
5. Refactor

## After Every Code Change

```bash
# Minimum verification (language-appropriate)
go test ./... && go vet ./...           # Go
bundle exec rspec && bundle exec rubocop # Ruby/Rails
pytest && mypy . && ruff check .         # Python
npm test && npm run lint                 # JS/TS
```

## Rules

- Tests BEFORE code. Always.
- Test output MUST be pristine (no warnings, no skips without reason)
- Every project needs: unit + integration + e2e
- Skip tests ONLY with explicit: "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"
- After writing code: list what could break, suggest tests to cover it

## Bug Fix Process

1. Write test that reproduces the bug
2. Confirm test fails
3. Fix the code
4. Confirm test passes
5. Check for regressions
