# ABOUTME: Agent loop meta-instructions for autonomous prompt optimization
# ABOUTME: Karpathy autoresearch pattern: edit prompt, eval, keep/revert

# Autoresearch Prompt Optimization Loop

You are an autonomous prompt optimization agent. Your goal: maximize the evaluation score by iteratively improving `prompt.md`.

## Loop

```
1. BASELINE  -> Run: uv run -- autoresearch-prompt evaluate
2. ANALYZE   -> Read results, identify failure patterns (wrong action, wrong category)
3. HYPOTHESIZE -> Form a specific hypothesis about why the prompt fails on those cases
4. EDIT      -> Make ONE targeted change to prompt.md (not multiple changes at once)
5. EVALUATE  -> Run eval again
6. COMPARE   -> If score improved: KEEP. If score regressed or unchanged: REVERT.
7. LOG       -> Append a row to results.tsv with timestamp, score, and notes
8. REPEAT    -> Go to step 2 (max 10 iterations per session)
```

## Rules

- **One change at a time.** Isolate variables so you know what worked.
- **Never edit eval_set.jsonl.** The eval set is ground truth.
- **Never edit the scoring formula.** Improve the prompt, not the metric.
- **Revert on regression.** Use `git checkout prompt.md` to restore.
- **Log every attempt.** Even failed ones teach you something.
- **Stop when score >= 0.95** or after 10 iterations.

## Change types to try (in order of typical impact)

1. **Clarify boundaries** between extract and skip (most common failure mode)
2. **Add negative examples** for tricky skip cases (opinion pieces that look informative)
3. **Refine category descriptions** with distinguishing criteria
4. **Adjust output format** instructions (JSON structure, field expectations)
5. **Add edge case handling** (paywall teasers, non-English content, republished best-of)

## What NOT to change

- Do not add model-specific instructions (temperature, etc.) - those are API params
- Do not make the prompt longer than ~800 words (token cost matters)
- Do not add few-shot examples longer than 2-3 lines each
- Do not change the JSON output schema expected by the eval set

## Results.tsv format

```
timestamp	score	action_acc	category_acc	cost_usd	latency_ms	errors	model	notes
2026-03-16T10:00	0.85	0.90	0.83	0.0045	350	0	haiku-4.5	baseline
```

Column names for accuracy fields are dynamic: `{field}_acc` for each `expected_*` field in the eval set.
