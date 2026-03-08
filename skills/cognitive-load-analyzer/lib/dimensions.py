# ABOUTME: D1-D8 dimension normalization functions for the Cognitive Load Index
# ABOUTME: Each function takes raw metrics and returns a normalized score in (0, 1)

"""D1-D8 dimension normalization functions for the Cognitive Load Index.

Each function takes raw metrics and returns a normalized score in (0, 1).
All sigmoid parameters match the SKILL.md specification.
"""

from core import coefficient_of_variation, mean, p90, sigmoid


# --- D1: Structural Complexity (20%) ---


def normalize_d1(complexity_scores: list[float]) -> dict:
    """Normalize structural complexity scores."""
    if not complexity_scores:
        return {"d1": 0.0, "raw": 0.0, "mean": 0.0, "p90": 0.0}
    m = mean(complexity_scores)
    p = p90(complexity_scores)
    raw = 0.4 * m + 0.6 * p
    return {"d1": sigmoid(raw, midpoint=15, steepness=0.15), "raw": raw, "mean": m, "p90": p}


# --- D2: Nesting Depth (15%) ---


def normalize_d2(nesting_depths: list[float]) -> dict:
    """Normalize nesting depth scores."""
    if not nesting_depths:
        return {"d2": 0.0, "raw": 0.0, "mean": 0.0, "p90": 0.0}
    m = mean(nesting_depths)
    p = p90(nesting_depths)
    raw = 0.3 * m + 0.7 * p
    return {"d2": sigmoid(raw, midpoint=4, steepness=0.5), "raw": raw, "mean": m, "p90": p}


# --- D3: Volume and Size (12%) ---


def normalize_d3(
    func_locs: list[float],
    file_locs: list[float],
    param_counts: list[float],
    methods_per_class: list[float],
) -> dict:
    """Normalize volume and size metrics."""
    size_func = sigmoid(p90(func_locs), midpoint=30, steepness=0.05) if func_locs else 0.0
    size_file = sigmoid(p90(file_locs), midpoint=300, steepness=0.005) if file_locs else 0.0
    size_params = sigmoid(mean(param_counts), midpoint=4, steepness=0.5) if param_counts else 0.0
    size_class = sigmoid(p90(methods_per_class), midpoint=15, steepness=0.1) if methods_per_class else 0.0
    d3 = 0.35 * size_func + 0.25 * size_file + 0.20 * size_params + 0.20 * size_class
    return {
        "d3": d3,
        "size_func": size_func,
        "size_file": size_file,
        "size_params": size_params,
        "size_class": size_class,
    }


# --- D4: Naming Quality (15%) ---


def normalize_d4_static(
    short_name_proportion: float,
    abbreviation_density: float,
    single_char_per_100loc: float,
    consistency_ratio: float,
) -> dict:
    """Normalize D4 using static heuristics only."""
    naming_short = short_name_proportion
    naming_abbrev = abbreviation_density
    naming_single_char = sigmoid(single_char_per_100loc, midpoint=2, steepness=0.5)
    naming_consistency = 1.0 - consistency_ratio
    d4_static = (
        0.30 * naming_short
        + 0.25 * naming_abbrev
        + 0.25 * naming_single_char
        + 0.20 * naming_consistency
    )
    return {
        "d4_static": d4_static,
        "naming_short": naming_short,
        "naming_abbrev": naming_abbrev,
        "naming_single_char": naming_single_char,
        "naming_consistency": naming_consistency,
    }


def normalize_d4_with_llm(d4_static: float, llm_score: float) -> dict:
    """Combine static D4 with LLM semantic assessment."""
    d4 = 0.60 * d4_static + 0.40 * llm_score
    return {"d4": d4, "d4_static": d4_static, "llm_score": llm_score}


def normalize_d4_fallback(
    short_name_proportion: float,
    abbreviation_density: float,
    single_char_per_100loc: float,
    consistency_ratio: float,
    dictionary_coverage: float,
) -> dict:
    """Normalize D4 using fallback formula (no LLM)."""
    naming_short = short_name_proportion
    naming_abbrev = abbreviation_density
    naming_single_char = sigmoid(single_char_per_100loc, midpoint=2, steepness=0.5)
    naming_consistency = 1.0 - consistency_ratio
    dict_penalty = 1.0 - dictionary_coverage
    d4_fallback = (
        0.35 * naming_short
        + 0.30 * naming_abbrev
        + 0.15 * naming_single_char
        + 0.10 * naming_consistency
        + 0.10 * dict_penalty
    )
    return {
        "d4_fallback": d4_fallback,
        "naming_short": naming_short,
        "naming_abbrev": naming_abbrev,
        "naming_single_char": naming_single_char,
        "naming_consistency": naming_consistency,
        "dict_penalty": dict_penalty,
    }


# --- D5: Coupling (12%) ---


def normalize_d5(
    efferent_couplings: list[float],
    imports_per_file: list[float],
    afferent_couplings: list[float],
) -> dict:
    """Normalize coupling metrics."""
    epsilon = 1e-9
    ce_mean = mean(efferent_couplings) if efferent_couplings else 0.0
    coupling_efferent = sigmoid(ce_mean, midpoint=8, steepness=0.2)
    coupling_imports = (
        sigmoid(mean(imports_per_file), midpoint=10, steepness=0.15) if imports_per_file else 0.0
    )

    if efferent_couplings and afferent_couplings:
        n = min(len(efferent_couplings), len(afferent_couplings))
        instabilities = [
            efferent_couplings[i] / (afferent_couplings[i] + efferent_couplings[i] + epsilon)
            for i in range(n)
        ]
        instability_risk = mean(instabilities) * ce_mean
    else:
        instability_risk = 0.0

    instability_sigmoid = sigmoid(instability_risk, midpoint=5, steepness=0.2)
    d5 = 0.40 * coupling_efferent + 0.35 * coupling_imports + 0.25 * instability_sigmoid
    return {
        "d5": d5,
        "coupling_efferent": coupling_efferent,
        "coupling_imports": coupling_imports,
        "instability_risk": instability_risk,
        "instability_sigmoid": instability_sigmoid,
    }


# --- D6: Cohesion (10%) ---


def normalize_d6_class(lcom_values: list[float]) -> dict:
    """Normalize cohesion for class-based languages."""
    if not lcom_values:
        return {"d6": 0.0, "mean_lcom": 0.0}
    m = mean(lcom_values)
    return {"d6": sigmoid(m, midpoint=0.5, steepness=4), "mean_lcom": m}


def normalize_d6_module(
    avg_exports_used_together: float,
    total_exports: float,
) -> dict:
    """Normalize cohesion for functional/module-based languages."""
    if total_exports == 0:
        return {"d6": 0.0, "module_cohesion": 0.0}
    module_cohesion = 1.0 - (avg_exports_used_together / total_exports)
    return {"d6": sigmoid(module_cohesion, midpoint=0.4, steepness=4), "module_cohesion": module_cohesion}


# --- D7: Duplication (8%) ---


def normalize_d7(duplication_pct: float) -> dict:
    """Normalize duplication percentage. Input as fraction (0.05 = 5%)."""
    pct_100 = duplication_pct * 100
    return {"d7": sigmoid(pct_100, midpoint=5, steepness=0.3), "duplication_pct_100": pct_100}


# --- D8: Navigability (8%) ---


def normalize_d8(
    max_directory_depth: float,
    files_per_directory: list[float],
    file_sizes: list[float],
) -> dict:
    """Normalize navigability metrics."""
    nav_depth = sigmoid(max_directory_depth, midpoint=5, steepness=0.4)
    nav_density = sigmoid(p90(files_per_directory), midpoint=15, steepness=0.1) if files_per_directory else 0.0
    cv = coefficient_of_variation(file_sizes) if file_sizes else 0.0
    nav_variance = sigmoid(cv, midpoint=1.5, steepness=0.8)
    d8 = 0.35 * nav_depth + 0.35 * nav_density + 0.30 * nav_variance
    return {"d8": d8, "nav_depth": nav_depth, "nav_density": nav_density, "nav_variance": nav_variance}
