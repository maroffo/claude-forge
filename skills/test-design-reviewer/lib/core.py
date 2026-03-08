# ABOUTME: Pure math primitives for Farley Index calculation (sigmoid, p90, mean, LOC-weighted mean)
# ABOUTME: No external dependencies, uses only Python stdlib math

"""Pure math primitives for Farley Index calculation.

No external dependencies -- uses only Python stdlib math.
"""

import math


def sigmoid(x: float, midpoint: float, steepness: float) -> float:
    """Sigmoid normalization: 1 / (1 + e^(-steepness * (x - midpoint))).

    Overflow-safe: clamps the exponent to avoid math.exp overflow.
    Returns a value in (0, 1).
    """
    z = -steepness * (x - midpoint)
    if z > 500:
        return 0.0
    if z < -500:
        return 1.0
    return 1.0 / (1.0 + math.exp(z))


def p90(values: list[float]) -> float:
    """90th percentile via linear interpolation.

    Sorts, computes the index for the 90th percentile, and interpolates
    between adjacent values. Returns 0.0 for empty input.
    """
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = 0.9 * (n - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def mean(values: list[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty input."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def loc_weighted_mean(scores: list[float], locs: list[int]) -> float:
    """LOC-weighted mean for suite-level aggregation.

    Each score is weighted by the corresponding LOC count.
    Returns 0.0 if total LOC is 0 or inputs are empty.
    """
    if not scores or not locs:
        return 0.0
    total_loc = sum(locs)
    if total_loc == 0:
        return 0.0
    return sum(s * loc for s, loc in zip(scores, locs)) / total_loc
