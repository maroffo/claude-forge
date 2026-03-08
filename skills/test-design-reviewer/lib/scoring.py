# ABOUTME: Domain-specific scoring logic for the Farley Index (constants, normalization, blending, aggregation)
# ABOUTME: Builds on core.py math primitives; contains all formulas from farley-properties-and-scoring

"""Domain-specific scoring logic for the Farley Index.

Builds on core.py math primitives. Contains all constants and formulas
specified in farley-properties-and-scoring.md.
"""

from core import loc_weighted_mean, mean, p90, sigmoid

# --- Constants ---

PROPERTY_CODES = ["U", "M", "R", "A", "N", "G", "F", "T"]

WEIGHTS = {
    "U": 1.5,
    "M": 1.5,
    "R": 1.25,
    "A": 1.0,
    "N": 1.0,
    "G": 1.0,
    "F": 0.75,
    "T": 1.0,
}

WEIGHT_SUM = 9.0

RATING_SCALE = [
    (9.0, "Exemplary"),
    (7.5, "Excellent"),
    (6.0, "Good"),
    (4.5, "Fair"),
    (3.0, "Poor"),
    (0.0, "Critical"),
]

# Default sigmoid parameters per property.
# Each tuple: (neg_midpoint, neg_steepness, pos_midpoint, pos_steepness, neg_weight, pos_weight)
# All weights are 0.5/0.5 so that no signals -> 0.5*5.0 + 0.5*5.0 = 5.0
DEFAULT_SIGMOID_PARAMS = {
    "U": {"neg_midpoint": 0.30, "neg_steepness": 8.0, "pos_midpoint": 0.50, "pos_steepness": 8.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "M": {"neg_midpoint": 0.25, "neg_steepness": 8.0, "pos_midpoint": 0.40, "pos_steepness": 8.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "R": {"neg_midpoint": 0.15, "neg_steepness": 10.0, "pos_midpoint": 0.30, "pos_steepness": 10.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "A": {"neg_midpoint": 0.20, "neg_steepness": 8.0, "pos_midpoint": 0.40, "pos_steepness": 8.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "N": {"neg_midpoint": 0.20, "neg_steepness": 8.0, "pos_midpoint": 0.50, "pos_steepness": 8.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "G": {"neg_midpoint": 0.25, "neg_steepness": 8.0, "pos_midpoint": 0.40, "pos_steepness": 8.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "F": {"neg_midpoint": 0.10, "neg_steepness": 10.0, "pos_midpoint": 0.30, "pos_steepness": 10.0, "neg_weight": 0.5, "pos_weight": 0.5},
    "T": {"neg_midpoint": 0.30, "neg_steepness": 6.0, "pos_midpoint": 0.50, "pos_steepness": 6.0, "neg_weight": 0.5, "pos_weight": 0.5},
}


# --- Functions ---

def normalize_property(prop, neg_count, pos_count, total_methods, params=None):
    """Normalize a single property's signal counts to a 0-10 score.

    Uses sigmoid normalization on signal densities.
    Returns 5.0 when both counts are 0 (conservative base).
    """
    if params is None:
        params = DEFAULT_SIGMOID_PARAMS[prop]

    if total_methods == 0:
        return 5.0

    # No signals detected -> conservative base score per spec
    if neg_count == 0 and pos_count == 0:
        return 5.0

    neg_density = neg_count / total_methods
    pos_density = pos_count / total_methods

    neg_component = (1.0 - sigmoid(neg_density, params["neg_midpoint"], params["neg_steepness"])) * 10.0
    pos_component = sigmoid(pos_density, params["pos_midpoint"], params["pos_steepness"]) * 10.0

    return params["neg_weight"] * neg_component + params["pos_weight"] * pos_component


def blend_scores(static_score, llm_score, static_weight=0.6):
    """Blend static and LLM scores. Default 60/40 split."""
    return static_weight * static_score + (1.0 - static_weight) * llm_score


def compute_farley_index(property_scores):
    """Compute the Farley Index from 8 property scores.

    Takes a dict like {"U": 8.5, "M": 7.0, ...}.
    Returns the weighted index on a 0-10 scale.
    """
    weighted_sum = sum(
        property_scores[prop] * WEIGHTS[prop]
        for prop in PROPERTY_CODES
    )
    return weighted_sum / WEIGHT_SUM


def get_rating(farley_index):
    """Look up the rating string for a Farley Index value."""
    for threshold, rating in RATING_SCALE:
        if farley_index >= threshold:
            return rating
    return "Critical"


def aggregate_file(method_scores):
    """Aggregate per-method scores to file-level scores.

    Uses mean for positive signals, P90 for negative signals to surface
    worst offenders. method_scores is a list of dicts, each with keys
    for property codes mapping to {"neg": float, "pos": float} or just a float score.

    If method_scores contains simple float scores per property, returns
    their mean per property.
    """
    if not method_scores:
        return {prop: 5.0 for prop in PROPERTY_CODES}

    result = {}
    for prop in PROPERTY_CODES:
        scores = [m[prop] for m in method_scores if prop in m]
        if not scores:
            result[prop] = 5.0
        else:
            result[prop] = mean(scores)
    return result


def aggregate_file_split(method_neg_scores, method_pos_scores):
    """Aggregate per-method split scores to file-level scores.

    Uses P90 for negative signal scores (worst offenders surface)
    and mean for positive signal scores.
    """
    result = {}
    for prop in PROPERTY_CODES:
        neg_vals = [m[prop] for m in method_neg_scores if prop in m]
        pos_vals = [m[prop] for m in method_pos_scores if prop in m]
        neg_agg = p90(neg_vals) if neg_vals else 0.0
        pos_agg = mean(pos_vals) if pos_vals else 0.0
        result[prop] = {"neg": neg_agg, "pos": pos_agg}
    return result


def aggregate_suite(file_scores, file_locs):
    """LOC-weighted mean across files for each property.

    file_scores: list of dicts (one per file), each {"U": 8.5, "M": 7.0, ...}
    file_locs: list of ints (LOC per file, same order)
    """
    result = {}
    for prop in PROPERTY_CODES:
        scores = [f[prop] for f in file_scores]
        result[prop] = loc_weighted_mean(scores, file_locs)
    return result


def full_pipeline(data):
    """End-to-end calculation from raw signal counts.

    Input data format:
    {
        "properties": {
            "U": {"neg_count": 2, "pos_count": 8, "total_methods": 20},
            ...
        },
        "llm_scores": {"U": 8.0, "M": 7.5, ...},  // optional
        "static_weight": 0.6  // optional, default 0.6
    }

    Returns:
    {
        "static_scores": {"U": ..., ...},
        "blended_scores": {"U": ..., ...},  // only if llm_scores provided
        "farley_index": float,
        "rating": str
    }
    """
    static_weight = data.get("static_weight", 0.6)
    properties = data["properties"]
    llm_scores = data.get("llm_scores")

    # Phase 1: static normalization
    static_scores = {}
    for prop in PROPERTY_CODES:
        prop_data = properties.get(prop, {})
        static_scores[prop] = normalize_property(
            prop,
            prop_data.get("neg_count", 0),
            prop_data.get("pos_count", 0),
            prop_data.get("total_methods", 0),
        )

    # Phase 2: blend with LLM scores if provided
    if llm_scores:
        blended_scores = {}
        for prop in PROPERTY_CODES:
            blended_scores[prop] = blend_scores(
                static_scores[prop],
                llm_scores.get(prop, static_scores[prop]),
                static_weight,
            )
        final_scores = blended_scores
    else:
        blended_scores = None
        final_scores = static_scores

    farley_index = compute_farley_index(final_scores)
    rating = get_rating(farley_index)

    result = {
        "static_scores": static_scores,
        "farley_index": round(farley_index, 2),
        "rating": rating,
    }
    if blended_scores is not None:
        result["blended_scores"] = blended_scores
    return result
