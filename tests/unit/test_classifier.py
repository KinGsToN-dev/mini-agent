"""Тесты для agent/classifier.py — гибрид regex + LLM."""
from unittest.mock import MagicMock, patch

import pytest

from agent import classifier


class TestRegexFirst:

    @pytest.mark.unit
    def test_trading_goes_via_regex(self):
        """Трейдинг — regex уверенно, без LLM."""
        cat, conf, src = classifier.classify(
            "дай анализ по золоту и отправь в телеграм",
            available=["gemini", "groq", "mistral", "openrouter"],
        )
        assert cat == "trading"
        assert src == "regex"
        assert conf >= 0.7

    @pytest.mark.unit
    def test_vision_goes_via_regex(self):
        """Vision — regex (только Gemini)."""
        cat, conf, src = classifier.classify(
            "что на экране",
            available=["gemini", "groq"],
        )
        assert cat == "vision"
        assert src == "regex"

    @pytest.mark.unit
    def test_code_goes_via_regex(self):
        """Код — regex (Mistral)."""
        cat, conf, src = classifier.classify(
            "напиши функцию quicksort",
            available=["gemini", "groq", "mistral"],
        )
        assert cat == "code"
        assert src == "regex"


class TestLLMFallback:

    @pytest.mark.unit
    def test_unclear_query_goes_to_llm(self):
        """Неясный запрос → LLM."""
        with patch.object(classifier, "_classify_llm", return_value="trading"):
            classifier._classify_llm.cache_clear() if hasattr(classifier._classify_llm, "cache_clear") else None
            cat, conf, src = classifier.classify(
                "расскажи что-нибудь интересное",
                available=["gemini", "groq", "mistral", "openrouter"],
            )
        assert cat == "trading"
        assert src == "llm"
        assert conf >= 0.8

    @pytest.mark.unit
    def test_llm_unavailable_falls_back_to_regex(self):
        """LLM упал → fallback на regex."""
        with patch.object(classifier, "_classify_llm", return_value=None):
            cat, conf, src = classifier.classify(
                "расскажи что-нибудь",
                available=["gemini", "groq"],
            )
        # regex вернул general (не уверен) → fallback → general
        assert cat in ("general", "trading", "vision", "code", "web_search")
        assert src in ("fallback", "regex")

    @pytest.mark.unit
    def test_empty_query(self):
        cat, conf, src = classifier.classify("")
        assert cat == "general"
        assert src == "regex"


class TestLLMParsing:

    @pytest.mark.unit
    def test_llm_prompt_built(self):
        """Проверяем, что промпт формируется с текстом."""
        prompt = classifier.CLASSIFIER_PROMPT.format(text="test query")
        assert "test query" in prompt
        assert "trading" in prompt
        assert "general" in prompt

    @pytest.mark.unit
    def test_valid_categories(self):
        assert "trading" in classifier.VALID_CATEGORIES
        assert "vision" in classifier.VALID_CATEGORIES
        assert "code" in classifier.VALID_CATEGORIES
        assert "web_search" in classifier.VALID_CATEGORIES
        assert "general" in classifier.VALID_CATEGORIES
        assert len(classifier.VALID_CATEGORIES) == 5


class TestCache:

    @pytest.mark.unit
    def test_cache_exists(self):
        """У _classify_llm должен быть lru_cache."""
        assert hasattr(classifier._classify_llm, "cache_clear")
        assert hasattr(classifier._classify_llm, "cache_info")

    @pytest.mark.unit
    def test_clear_cache(self):
        """clear_cache() работает без ошибок."""
        classifier.clear_cache()  # не должно упасть
