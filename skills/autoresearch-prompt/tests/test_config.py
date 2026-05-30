# ABOUTME: Tests for config-driven model ID and pricing loaded from models.toml
# ABOUTME: Covers env override, default_model, price_for known/unknown, float coercion

from __future__ import annotations

from autoresearch_prompt.config import get_default_model, get_pricing, price_for


class TestGetDefaultModel:
    def test_env_override_wins(self, monkeypatch):
        monkeypatch.setenv("AUTORESEARCH_MODEL", "claude-sonnet-4-6")
        assert get_default_model() == "claude-sonnet-4-6"

    def test_empty_env_falls_back_to_toml(self, monkeypatch):
        monkeypatch.setenv("AUTORESEARCH_MODEL", "")
        assert get_default_model() == "claude-haiku-4-5-20251001"

    def test_toml_default_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("AUTORESEARCH_MODEL", raising=False)
        assert get_default_model() == "claude-haiku-4-5-20251001"


class TestPricing:
    def test_price_for_known_haiku(self):
        assert price_for("claude-haiku-4-5-20251001") == (1.00, 5.00)

    def test_price_for_known_sonnet(self):
        assert price_for("claude-sonnet-4-6") == (3.00, 15.00)

    def test_price_for_unknown_returns_zero(self):
        assert price_for("claude-opus-does-not-exist") == (0.0, 0.0)

    def test_price_for_unknown_does_not_raise(self):
        # must not raise on any string, including empty
        assert price_for("") == (0.0, 0.0)

    def test_get_pricing_values_are_floats(self):
        pricing = get_pricing()
        assert pricing  # non-empty
        for in_price, out_price in pricing.values():
            assert isinstance(in_price, float)
            assert isinstance(out_price, float)
