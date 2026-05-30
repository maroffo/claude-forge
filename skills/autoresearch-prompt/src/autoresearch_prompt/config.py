# ABOUTME: Config-driven model ID and token pricing loaded from models.toml
# ABOUTME: Eliminates hardcoded model drift; env AUTORESEARCH_MODEL overrides default

from __future__ import annotations

import os
import tomllib
from functools import lru_cache
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent / "models.toml"


@lru_cache(maxsize=1)
def _load() -> dict:
    """Load and cache models.toml. Degrade to empty config if the file is missing."""
    try:
        with _CONFIG_PATH.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}


def get_default_model() -> str:
    """Resolve the default model.

    Precedence: env ``AUTORESEARCH_MODEL`` (if set and non-empty), then the toml
    ``default_model``, then ``""``.
    """
    env = os.environ.get("AUTORESEARCH_MODEL")
    if env:
        return env
    return _load().get("default_model", "")


def get_pricing() -> dict[str, tuple[float, float]]:
    """Return the ``[pricing]`` table as model_id -> (input_per_1M, output_per_1M) floats."""
    raw = _load().get("pricing", {})
    return {model: (float(prices[0]), float(prices[1])) for model, prices in raw.items()}


def price_for(model: str) -> tuple[float, float]:
    """Return pricing for *model*, or ``(0.0, 0.0)`` if unknown. Never raises."""
    return get_pricing().get(model, (0.0, 0.0))
