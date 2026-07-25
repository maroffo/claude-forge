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

**Scoring methodology:**
- **Static scoring**: compute 0-10 per property using sigmoid normalization on signal densities (negative signals / test methods, positive signals / test methods). Use `lib/cli_calculator.py` for deterministic math (JSON in, JSON out).
- **LLM scoring**: assess holistically per property, focusing on semantic aspects static analysis misses (naming quality, assertion appropriateness, tautology theatre)
- **Blend**: `final_property_score = 0.60 * static_score + 0.40 * llm_score` per property
- **Conservative default**: when no signals detected for a property, default to 5.0 (unknown quality, not good quality)

**Per-property scoring rubrics:** anchor each 0-10 score to the full 8-properties x 5-bands matrix in `references/bands.md`. Rough guide: 9-10 exemplary, 7-8 strong, 5-6 mixed, 3-4 weak, 1-2 harmful.

**Aggregation methodology:**
- **Per-test-method**: collect signals at individual method level
- **Per-test-file**: mean for positive signals, P90 for negative signals (worst offenders must surface)
- **Per-test-suite**: LOC-weighted mean across files

**Sampling for large suites:**
- Under 50 test files: analyze all
- Over 50: SHA-256 deterministic selection (30%) plus all files exceeding 100 test methods

**Weighted Farley Index** = `(U*1.5 + M*1.5 + R*1.25 + A*1.0 + N*1.0 + G*1.0 + F*0.75 + T*1.0) / 9.0`

Divisor is 9.0 (sum of weights), not 8 (number of properties). U/M weighted highest (readability, coupling); F weighted lowest (speed is contextual).

| Range | Rating | Interpretation |
|-------|--------|----------------|
| 9.0-10.0 | Exemplary | Model suite; tests serve as living documentation |
| 7.5-8.9 | Excellent | High quality with minor improvement opportunities |
| 6.0-7.4 | Good | Solid foundation with clear areas for improvement |
| 4.5-5.9 | Fair | Functional but needs significant attention to test design |
| 3.0-4.4 | Poor | Tests provide limited value; major refactoring needed |
| 0.0-2.9 | Critical | Tests may be harmful; consider rewriting from scratch |

### Step 3: Tautology Theatre Detection

The critical question: **"Would this test still pass if all production code were deleted?"**

Scan for these 4 patterns:

| Pattern | What it looks like | Example |
|---------|--------------------|---------|
| **Mock tautology** | Test verifies that a mock returns what it was told to return | `mock.return_value = 42; assert service.get() == 42` (only tests the mock) |
| **Mock-only test** | Every dependency is mocked, nothing real executes | Test with 5 mocks and zero real objects |
| **Trivial tautology** | Assertion is always true regardless of code | `assert isinstance(result, dict)` when function signature guarantees dict |
| **Framework test** | Tests framework behavior, not application logic | Testing that Rails validations work, that pytest fixtures inject |

Also scan for **mock interaction anti-patterns** (affect Maintainable score):

| Pattern | What it looks like |
|---------|--------------------|
| **Over-specified interactions** | verify with exact call counts, call ordering, verifyNoMoreInteractions |
| **Testing internal details** | ArgumentCaptor deep inspection, verify(never()) mirroring branches, high verify-to-assert ratio |

For each tautology or anti-pattern found: report the file, line, pattern type, and why it's problematic.

### Step 4: Report

```markdown
## Test Design Review

### Farley Index: X.X / 10.0 (Rating)

| Property | Static | LLM | Blended | Weight | Weighted | Key Evidence |
|----------|--------|-----|---------|--------|----------|--------------|
| Understandable | X.X | X.X | X.X | 1.50x | X.XX | ... |
| Maintainable | X.X | X.X | X.X | 1.50x | X.XX | ... |
| Repeatable | X.X | X.X | X.X | 1.25x | X.XX | ... |
| Atomic | X.X | X.X | X.X | 1.00x | X.XX | ... |
| Necessary | X.X | X.X | X.X | 1.00x | X.XX | ... |
| Granular | X.X | X.X | X.X | 1.00x | X.XX | ... |
| Fast | X.X | X.X | X.X | 0.75x | X.XX | ... |
| First (TDD) | X.X | X.X | X.X | 1.00x | X.XX | ... |

### Tautology Theatre Analysis

Each subsection always present; use "None detected." when empty.

#### Mock Tautologies
| Test Method | Line | Mock Setup | Assertion |
#### Mock-Only Tests
| Test Method | Line | Evidence |
#### Trivial Tautologies
| Test Method | Line | Assertion |
#### Framework Tests
| Test Method | Line | Assertion | What It Actually Tests |

**Summary**: {total} instances across {affected}/{total_methods} test methods.

### Top 3 Improvements
1. [Highest-impact fix targeting weakest high-weight property]
2. [Second priority]
3. [Third priority]

### Methodology Notes
- Static/LLM blend: 60/40
- Files analyzed: {count} ({sampling note})
- Language: {lang}, Framework: {framework}
```

## Integration with Review Pipeline

This skill is invoked by the orchestrator when test files are in scope (see the `orchestrator` skill, review routing step). Can also be invoked directly via `/test-design-reviewer`.

## Deterministic Scoring Calculator

`lib/cli_calculator.py` provides JSON-in, JSON-out math for reproducible scores. Delegate all Farley Index arithmetic to this CLI to avoid LLM rounding drift.

Commands: `normalize-property`, `blend-scores`, `compute-farley`, `get-rating`, `aggregate-file`, `aggregate-suite`, `full-pipeline`.

```bash
# Normalize a single property from signal counts
uv run python3 lib/cli_calculator.py normalize-property '{"prop":"U","neg_count":2,"pos_count":8,"total_methods":20}'

# Compute Farley Index from 8 blended scores
uv run python3 lib/cli_calculator.py compute-farley '{"U":8.5,"M":7.0,"R":9.0,"A":8.0,"N":7.5,"G":8.0,"F":6.0,"T":7.0}'

# End-to-end: raw signals + optional LLM scores -> index + rating
uv run python3 lib/cli_calculator.py full-pipeline '{"properties":{"U":{"neg_count":2,"pos_count":8,"total_methods":20},...},"llm_scores":{"U":8.0,...}}'
```

## Common Issues

| Issue | Solution |
|-------|----------|
| No test files found | Check file patterns; some projects use non-standard locations |
| High mock count ≠ bad | Mocks are fine when testing boundaries; flag only when they replace all real logic |
| Property scores vary by test type | Score unit tests and integration tests separately if the suite is mixed |
| Legacy test suite scores low | Focus improvements on the top 3, not a full rewrite |
