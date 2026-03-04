---
name: test-design-reviewer
description: "Assess test suite quality using Farley's 8 Properties and Tautology Theatre detection. Use when user says review tests, test quality, are my tests good, test assessment, or test design review. Not for writing tests (use language skills) or code review (use gemini-review)."
---

# ABOUTME: Test quality assessment using Farley's 8 Properties of Good Tests
# ABOUTME: Detects tautological tests, mock theatre, and structural test weaknesses

# Test Design Reviewer

## Quality Notes

- Read every test file thoroughly before scoring
- Quality over speed: analyze what each test actually verifies
- Do not skip the Tautology Theatre check

## Process

### Step 1: Collect test files

Identify all test files in scope. Use language-appropriate patterns:
- Go: `*_test.go`
- Python: `test_*.py`, `*_test.py`
- Ruby: `*_spec.rb`
- JS/TS: `*.test.ts`, `*.spec.ts`

### Step 2: Score against Farley's 8 Properties

Rate each property 0-10 across the test suite. Provide evidence.

| # | Property | Question to ask | Red flags |
|---|----------|-----------------|-----------|
| 1 | **Understandable** | Can you tell what's being tested in 5 seconds? | Cryptic names, no arrange/act/assert structure, shared state |
| 2 | **Maintainable** | Will this break when implementation changes? | Testing private methods, brittle selectors, hardcoded values |
| 3 | **Repeatable** | Same result every run, any order, any machine? | Time-dependent, filesystem-dependent, test ordering, shared DB state |
| 4 | **Atomic** | One reason to fail? | Multiple assertions testing different behaviors, setup-heavy |
| 5 | **Necessary** | Does this test earn its keep? | Duplicate coverage, testing framework/language behavior |
| 6 | **Granular** | Pinpoints the failure location? | Coarse assertions (`assert result`), catch-all tests |
| 7 | **Fast** | Runs in milliseconds? | Real HTTP calls, sleep/wait, full DB setup per test |
| 8 | **First** | Written before production code? | Tests that mirror implementation structure, not behavior |

**Farley Index** = average of 8 scores (0-10 scale).

| Range | Verdict |
|-------|---------|
| 8-10 | Excellent test design |
| 6-7.9 | Solid, minor improvements possible |
| 4-5.9 | Significant weaknesses |
| 0-3.9 | Test theatre: tests exist but provide false confidence |

### Step 3: Tautology Theatre Detection

The critical question: **"Would this test still pass if all production code were deleted?"**

Scan for these 4 patterns:

| Pattern | What it looks like | Example |
|---------|--------------------|---------|
| **Mock tautology** | Test verifies that a mock returns what it was told to return | `mock.return_value = 42; assert service.get() == 42` (only tests the mock) |
| **Mock-only test** | Every dependency is mocked, nothing real executes | Test with 5 mocks and zero real objects |
| **Trivial tautology** | Assertion is always true regardless of code | `assert isinstance(result, dict)` when function signature guarantees dict |
| **Framework test** | Tests framework behavior, not application logic | Testing that Rails validations work, that pytest fixtures inject |

For each found: report the file, line, pattern type, and why it's tautological.

### Step 4: Report

```markdown
## Test Design Review

### Farley Index: X.X/10 [Verdict]

| Property | Score | Evidence |
|----------|------:|----------|
| Understandable | X | ... |
| ... | ... | ... |

### Tautology Theatre: X found

| File:Line | Pattern | Issue |
|-----------|---------|-------|
| ... | Mock tautology | ... |

### Top 3 Improvements
1. [Most impactful fix]
2. [Second priority]
3. [Third priority]
```

## Integration with Review Pipeline

This skill is invoked by the orchestrator when test files are in scope (see `orchestrator-protocol.md`, review routing step). Can also be invoked directly via `/test-design-reviewer`.

## Common Issues

| Issue | Solution |
|-------|----------|
| No test files found | Check file patterns; some projects use non-standard locations |
| High mock count ≠ bad | Mocks are fine when testing boundaries; flag only when they replace all real logic |
| Property scores vary by test type | Score unit tests and integration tests separately if the suite is mixed |
| Legacy test suite scores low | Focus improvements on the top 3, not a full rewrite |
