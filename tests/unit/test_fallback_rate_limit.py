"""Тесты для providers/fallback.py — детекция rate_limit и unavailable."""
from unittest.mock import MagicMock

import pytest

from providers.fallback import is_rate_limit, is_unavailable


class TestIsRateLimit:

    @pytest.mark.unit
    @pytest.mark.parametrize("msg", [
        "Rate limit exceeded for model X",
        "rate_limit_exceeded: something",
        "429 Too Many Requests",
        "too many requests for this model",
        "ratelimit exceeded",
    ])
    def test_detects_rate_limit(self, msg):
        exc = RuntimeError(msg)
        assert is_rate_limit(exc) is True, f"'{msg}' должен ловиться"

    @pytest.mark.unit
    @pytest.mark.parametrize("msg", [
        "Model not found",
        "Connection timeout",
        "Some random error",
    ])
    def test_not_rate_limit(self, msg):
        exc = RuntimeError(msg)
        assert is_rate_limit(exc) is False, f"'{msg}' НЕ должен ловиться"


class TestIsUnavailable:

    @pytest.mark.unit
    @pytest.mark.parametrize("msg", [
        "404 NOT_FOUND",
        "model not found",
        "no longer available to new users",
        "Requested entity was not found",
    ])
    def test_detects_unavailable(self, msg):
        exc = RuntimeError(msg)
        assert is_unavailable(exc) is True, f"'{msg}' должен ловиться"

    @pytest.mark.unit
    def test_rate_limit_is_not_unavailable(self):
        exc = RuntimeError("Rate limit exceeded")
        assert is_unavailable(exc) is False
