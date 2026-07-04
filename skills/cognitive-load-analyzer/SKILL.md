---
name: cognitive-load-analyzer
description: "Calculate a Cognitive Load Index (CLI) score (0-1000) for a codebase. Measures 8 dimensions of cognitive load using static analysis and LLM-based naming assessment."
tools: Read, Grep, Glob, Bash, Write, AskUserQuestion
---

# ABOUTME: Measures cognitive load of codebases using 8 dimensions, producing a 0-1000 score
# ABOUTME: Sigmoid-normalized metrics with P90 weighting, Python calculator for deterministic results

# Cognitive Load Analyzer

Produce a deterministic Cognitive Load Index (0-1000) with per-dimension breakdown and actionable recommendations.

**When to run:** before major refactors, when onboarding to unfamiliar codebases, during architecture reviews, or to track complexity trends over time.

## Scoring Scale

| CLI Score | Rating |
|-----------|--------|
| 0-100 | Excellent |
| 101-250 | Good |
| 251-400 | Moderate |
| 401-600 | Concerning |
| 601-800 | Poor |
| 801-999 | Severe |

Score is asymptotic: 0 and 1000 are unreachable by design. Cap at 999.

## The 8 Dimensions

| # | Dimension | Weight | Sigmoid(mid, steep) | Raw Input |
|---|-----------|--------|---------------------|-----------|
| D1 | Structural Complexity | 0.20 | (15, 0.15) | 0.4*mean + 0.6*P90 of CogC per function |
| D2 | Nesting Depth | 0.15 | (4, 0.5) | 0.3*mean + 0.7*P90 of max nest per function |
| D3 | Volume/Size | 0.12 | composite | 4 sub-sigmoids (func LOC, file LOC, params, methods) |
| D4 | Naming Quality | 0.15 | (2, 0.5) for single-char | Static heuristics + optional LLM assessment (60/40) |
| D5 | Coupling | 0.12 | (8, 0.2) efferent | Efferent coupling, imports, instability risk |
| D6 | Cohesion | 0.10 | (0.5, 4) class | LCOM per class or module cohesion ratio |
| D7 | Duplication | 0.08 | (5, 0.3) | Duplication % * 100 |
| D8 | Navigability | 0.08 | composite | Dir depth, files/dir P90, file size CV |

Weights sum to 1.00.

### Sigmoid Normalization

All raw metrics pass through: `sigmoid(x, mid, steep) = 1 / (1 + e^(-steep * (x - mid)))`

This guarantees smooth transitions and bounded output in (0, 1).

### P90 Weighting

Averages mask complexity. A few terrible functions among many simple ones must surface. Dimensions D1 and D2 weight P90 at 60-70% of the raw score.

### D3 Sub-components

```
size_func   = sigmoid(P90(LOC_f),     30,  0.05)   weight: 0.35
size_file   = sigmoid(P90(LOC_file),  300, 0.005)   weight: 0.25
size_params = sigmoid(mean(params_f), 4,   0.5)     weight: 0.20
size_class  = sigmoid(P90(methods_c), 15,  0.1)     weight: 0.20
```

### D4 Naming Quality

Static sub-components: short names (<3 chars), abbreviation density, single-char vars/100 LOC, convention consistency.

With LLM assessment: `D4 = 0.60 * D4_static + 0.40 * llm_score`
Without LLM: fallback formula adds dictionary coverage (10% weight).

LLM reproducibility: temperature 0, 20 identifiers/file via SHA-256 deterministic selection, score 0.0 (clear) to 1.0 (cryptic).

### D5 Coupling

```
D5 = 0.40 * sigmoid(mean(Ce), 8, 0.2)
   + 0.35 * sigmoid(mean(imports), 10, 0.15)
   + 0.25 * sigmoid(instability_risk, 5, 0.2)
```

### D8 Navigability

```
D8 = 0.35 * sigmoid(max_dir_depth, 5, 0.4)
   + 0.35 * sigmoid(P90(files_per_dir), 15, 0.1)
   + 0.30 * sigmoid(cv_file_sizes, 1.5, 0.8)
```

## Aggregation

```
CLI_raw = sum(weight_i * D_i)
```

### Interaction Penalty

When both dimensions in a pair exceed 0.6, add +50 points each:

| Pair | Rationale |
|------|-----------|
| D1 + D2 | Complex + deeply nested |
| D4 + D3 | Poor names + large functions |
| D5 + D6 | High coupling + low cohesion |

`CLI = min(999, round((CLI_raw + interaction_penalty) * 1000))`

Maximum penalty: +150 points.

## Workflow

### Phase 1: Discovery (2-3 turns)
1. Detect language(s) from file extensions
2. Count files, directories, LOC
3. Probe tools: `command -v lizard radon jscpd gocyclo`
4. If >100K LOC, activate deterministic sampling (SHA-256 hash mod 100 < 30, plus all files >200 LOC)

### Phase 2: Dimension Collection (8-12 turns)
For each D1-D8:
1. Run tool or fallback command to collect raw metrics
2. Invoke calculator: `python3 <skill_dir>/lib/cli_calculator.py normalize-d<N> '<json>'`
3. Record: raw metrics, normalized score, tool used, warnings

**Tool priority:** lizard (30+ languages) > language-specific (radon, gocyclo, eslint) > grep/awk/find heuristics.

### Phase 3: Aggregation (2-3 turns)
1. Pass all scores: `python3 <skill_dir>/lib/cli_calculator.py aggregate '{"D1": ..., "D8": ...}'`
2. Identify top 3 dimensions and top 5 worst offenders
3. Produce report

## Calculator Commands

Script path: `skills/cognitive-load-analyzer/lib/cli_calculator.py`

| Command | Input JSON | Output |
|---------|-----------|--------|
| `normalize-d1` | `{"complexity_scores": [...]}` | d1, raw, mean, p90 |
| `normalize-d2` | `{"nesting_depths": [...]}` | d2, raw, mean, p90 |
| `normalize-d3` | `{"func_locs": [...], "file_locs": [...], "param_counts": [...], "methods_per_class": [...]}` | d3 + sub-scores |
| `normalize-d4-static` | `{"short_name_proportion": f, "abbreviation_density": f, "single_char_per_100loc": f, "consistency_ratio": f}` | d4_static + components |
| `normalize-d4-llm` | `{"d4_static": f, "llm_score": f}` | d4 combined |
| `normalize-d5` | `{"efferent_couplings": [...], "imports_per_file": [...], "afferent_couplings": [...]}` | d5 + components |
| `normalize-d6-class` | `{"lcom_values": [...]}` | d6, mean_lcom |
| `normalize-d6-module` | `{"avg_exports_used_together": f, "total_exports": f}` | d6, module_cohesion |
| `normalize-d7` | `{"duplication_pct": f}` | d7 (input as fraction, e.g. 0.05) |
| `normalize-d8` | `{"max_directory_depth": f, "files_per_directory": [...], "file_sizes": [...]}` | d8 + components |
| `aggregate` | `{"D1": f, ..., "D8": f}` | cli_score, rating, penalty |
| `sample-files` | `{"file_paths": [...], "file_locs": {...}}` | selected files |

All output is `{"ok": true, "result": {...}}` or `{"ok": false, "error": "..."}`.

## Report Format

```
# Cognitive Load Index Report

## Summary
- CLI Score: {score} / 1000 ({rating})
- Language: {lang} | Files: {count} | LOC: {loc}
- D4 Mode: {llm_model | static_heuristic}

## Dimension Breakdown
| Dimension | Raw | Normalized | Weighted | Rating |
|-----------|-----|------------|----------|--------|
| D1-D8 rows... |
| Interaction Penalty | {pairs} | | +{pts} | |
| **TOTAL** | | | **{cli}** | **{rating}** |

## Top 5 Worst Offenders
1. {file:function} - {metrics}

## Recommendations
1. {action targeting highest-contributing dimension}

## Methodology
- Tools: {list} | Fallbacks: {list or "none"}
- Sampling: {full | SHA256 deterministic N%}
```

## Recommended Actions by Dimension

| Dimension | High Score Indicates | Fix |
|-----------|---------------------|-----|
| D1 | Complex control flow | Extract methods, replace conditionals with polymorphism |
| D2 | Deep nesting | Guard clauses (early returns), extract nested blocks |
| D3 | Oversized units | Split functions (<30 LOC), files (<300 LOC), parameter objects |
| D4 | Poor identifiers | Rename for intent, eliminate abbreviations |
| D5 | Tight dependencies | Dependency inversion, interfaces, reduce imports |
| D6 | Mixed responsibilities | SRP, split classes by responsibility |
| D7 | Duplicated code | Extract shared logic, parameterize |
| D8 | Poor organization | Flatten dirs, group related files |

Prioritize higher-weighted dimensions (D1, D4) over lower ones (D7, D8).

## Polyglot Codebases

Analyze each language subset independently, aggregate weighted by LOC:
`CLI_polyglot = sum(LOC_lang / LOC_total * CLI_lang)`

## Large Codebase Sampling (>100K LOC)

```python
selected = [f for f in sorted(files)
            if int(hashlib.sha256(f.encode()).hexdigest()[:8], 16) % 100 < 30]
# Plus all files > 200 LOC
```

Deterministic: identical results across runs for same codebase.
