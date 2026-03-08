# ABOUTME: Aggregation functions for computing the final Cognitive Load Index score
# ABOUTME: Combines 8 dimension scores into a single CLI score (0-999) with interaction penalties

"""Aggregation functions for computing the final Cognitive Load Index score.

Combines 8 dimension scores into a single CLI score (0-999).
"""

from collections import namedtuple


WEIGHTS = {
    "D1": 0.20,
    "D2": 0.15,
    "D3": 0.12,
    "D4": 0.15,
    "D5": 0.12,
    "D6": 0.10,
    "D7": 0.08,
    "D8": 0.08,
}

INTERACTION_PAIRS = [
    ("D1", "D2"),  # complexity + nesting
    ("D4", "D3"),  # poor naming + large functions
    ("D5", "D6"),  # high coupling + low cohesion
]

INTERACTION_PENALTY_PER_PAIR = 0.05

RATING_THRESHOLDS = [
    (100, "Excellent"),
    (250, "Good"),
    (400, "Moderate"),
    (600, "Concerning"),
    (800, "Poor"),
    (999, "Severe"),
]

CLIResult = namedtuple(
    "CLIResult",
    ["cli_score", "rating", "cli_raw", "interaction_penalty", "weighted_components"],
)


def compute_weighted_sum(dimension_scores: dict[str, float]) -> float:
    """Compute weighted sum of dimension scores."""
    return sum(WEIGHTS[k] * dimension_scores.get(k, 0.0) for k in WEIGHTS)


def compute_interaction_penalty(dimension_scores: dict[str, float]) -> float:
    """Compute interaction penalty for compounding dimension pairs.

    Adds 0.05 per pair where both dimensions exceed 0.6.
    Returns 0.0, 0.05, 0.10, or 0.15.
    """
    penalty = 0.0
    for d_a, d_b in INTERACTION_PAIRS:
        if dimension_scores.get(d_a, 0.0) > 0.6 and dimension_scores.get(d_b, 0.0) > 0.6:
            penalty += INTERACTION_PENALTY_PER_PAIR
    return penalty


def compute_cli_score(dimension_scores: dict[str, float]) -> CLIResult:
    """Compute the full CLI score from dimension scores."""
    cli_raw = compute_weighted_sum(dimension_scores)
    penalty = compute_interaction_penalty(dimension_scores)
    cli_score = min(999, round((cli_raw + penalty) * 1000))
    weighted = {k: round(WEIGHTS[k] * dimension_scores.get(k, 0.0), 6) for k in WEIGHTS}
    return CLIResult(
        cli_score=cli_score,
        rating=get_rating(cli_score),
        cli_raw=cli_raw,
        interaction_penalty=penalty,
        weighted_components=weighted,
    )


def get_rating(score: int) -> str:
    """Map a CLI score (0-999) to a rating string."""
    for threshold, rating in RATING_THRESHOLDS:
        if score <= threshold:
            return rating
    return "Severe"


def aggregate_polyglot(language_scores: dict[str, dict]) -> dict:
    """Aggregate CLI scores across languages, weighted by LOC."""
    total_loc = sum(entry["loc"] for entry in language_scores.values())
    if total_loc == 0:
        return {"cli_score": 0, "rating": "Excellent", "breakdown": {}}
    weighted_score = sum(
        entry["loc"] / total_loc * entry["cli_score"] for entry in language_scores.values()
    )
    cli_score = min(999, round(weighted_score))
    breakdown = {
        lang: {
            "cli_score": entry["cli_score"],
            "loc": entry["loc"],
            "weight": round(entry["loc"] / total_loc, 4),
        }
        for lang, entry in language_scores.items()
    }
    return {"cli_score": cli_score, "rating": get_rating(cli_score), "breakdown": breakdown}
