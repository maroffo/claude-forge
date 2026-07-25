# ABOUTME: Deterministic scoring calculator CLI and common troubleshooting issues for test design reviewer
# ABOUTME: Read when calculating Farley Index scores or troubleshooting test-design-reviewer errors

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
