# ABOUTME: Per-dimension formula derivations, sub-weights, and sigmoid math for the CLI score
# ABOUTME: Reference for the cognitive-load-analyzer skill; the Python calculator is the source of truth

# Cognitive Load Index Formulas

The `lib/cli_calculator.py` script is the deterministic source of truth for all arithmetic. This file documents the derivations behind its normalization commands so results can be audited and explained.

## Sigmoid Normalization

All raw metrics pass through: `sigmoid(x, mid, steep) = 1 / (1 + e^(-steep * (x - mid)))`

This guarantees smooth transitions and bounded output in (0, 1).

## P90 Weighting

Averages mask complexity. A few terrible functions among many simple ones must surface. Dimensions D1 and D2 weight P90 at 60-70% of the raw score.

## D1 Structural Complexity

Weight 0.20. Sigmoid `(mid=15, steep=0.15)`. Raw input: `0.4*mean + 0.6*P90` of Cognitive Complexity per function.

## D2 Nesting Depth

Weight 0.15. Sigmoid `(mid=4, steep=0.5)`. Raw input: `0.3*mean + 0.7*P90` of max nesting per function.

## D3 Volume/Size

Weight 0.12. Composite of 4 sub-sigmoids:

```
size_func   = sigmoid(P90(LOC_f),     30,  0.05)   weight: 0.35
size_file   = sigmoid(P90(LOC_file),  300, 0.005)   weight: 0.25
size_params = sigmoid(mean(params_f), 4,   0.5)     weight: 0.20
size_class  = sigmoid(P90(methods_c), 15,  0.1)     weight: 0.20
```

## D4 Naming Quality

Weight 0.15. Sigmoid `(mid=2, steep=0.5)` for single-char density.

Static sub-components: short names (<3 chars), abbreviation density, single-char vars/100 LOC, convention consistency.

With LLM assessment: `D4 = 0.60 * D4_static + 0.40 * llm_score`
Without LLM: fallback formula adds dictionary coverage (10% weight).

LLM reproducibility: temperature 0, 20 identifiers/file via SHA-256 deterministic selection, score 0.0 (clear) to 1.0 (cryptic).

## D5 Coupling

Weight 0.12. Efferent-coupling sigmoid `(mid=8, steep=0.2)`.

```
D5 = 0.40 * sigmoid(mean(Ce), 8, 0.2)
   + 0.35 * sigmoid(mean(imports), 10, 0.15)
   + 0.25 * sigmoid(instability_risk, 5, 0.2)
```

## D6 Cohesion

Weight 0.10. Class sigmoid `(mid=0.5, steep=4)`. Raw input: LCOM per class or module cohesion ratio.

## D7 Duplication

Weight 0.08. Sigmoid `(mid=5, steep=0.3)`. Raw input: duplication % * 100.

## D8 Navigability

Weight 0.08. Composite:

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
