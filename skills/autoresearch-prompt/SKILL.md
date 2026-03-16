# ABOUTME: Skill definition for autonomous prompt optimization via eval loop
# ABOUTME: Karpathy autoresearch pattern applied to LLM prompt engineering

---
name: autoresearch-prompt
description: Autonomous prompt optimization via eval-driven experiment loop
version: 0.1.0
triggers:
  - autoresearch
  - prompt optimization
  - optimize prompt
  - eval loop
---

# Autoresearch Prompt

Autonomous prompt optimization using Karpathy's autoresearch pattern. An agent edits `prompt.md`, runs eval against labeled examples, keeps improvements, reverts regressions.

## Quick start

```bash
cd skills/autoresearch-prompt

# Install
uv sync

# Run evaluation (needs ANTHROPIC_API_KEY)
uv run -- autoresearch-prompt evaluate

# Run with custom prompt/eval set
uv run -- autoresearch-prompt evaluate --prompt /path/to/prompt.md --eval-set /path/to/eval.jsonl

# Run with a different model
uv run -- autoresearch-prompt evaluate --model claude-sonnet-4-5-20250514
```

## Architecture

```
prompt.md          <- Agent edits this (system + user template)
eval_set.jsonl     <- 20 labeled examples (ground truth, never edit)
program.md         <- Agent loop instructions
results.tsv        <- Score history
src/               <- Eval harness (CLI + scoring + API calls)
```

## Scoring

```
score = 0.6 * extract_accuracy + 0.4 * category_accuracy
```

- `extract_accuracy`: fraction of correct extract/skip decisions
- `category_accuracy`: fraction of correct categories (among extracted examples only)
- When no category comparisons possible: `category_accuracy = 1.0`

## Output format

```
score: 0.85
extract_acc: 0.90
category_acc: 0.83
cost: $0.0045
latency_ms: 350
errors: 0
total: 20
```

## Running the optimization loop

Follow `program.md` instructions. The loop:
1. Run baseline eval
2. Analyze failures
3. Make ONE change to prompt.md
4. Re-eval
5. Keep improvement or revert regression
6. Log to results.tsv
7. Repeat (max 10 iterations)

## Adding eval examples

Add JSONL lines to `eval_set.jsonl`:

```json
{"from": "Sender <email>", "subject": "...", "content": "...", "expected_action": "extract", "expected_category": "AI Agents and Tools", "expected_content": "Brief expected insight"}
{"from": "Sender <email>", "subject": "...", "content": "...", "expected_action": "skip"}
```

## Prompt template format

`prompt.md` uses `## System` / `## User` markdown headers. Template variables: `{{from}}`, `{{subject}}`, `{{content}}`.
