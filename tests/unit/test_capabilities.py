"""Тесты для providers/capabilities.py — выбор провайдера с учётом tools."""
import pytest

from providers.capabilities import (
    PROVIDER_CAPABILITIES,
    describe_capabilities,
    pick_provider_for_category,
    provider_supports_tools,
    user_needs_tools,
)


ALL = ["gemini", "groq", "mistral", "openrouter"]


# ============================================================
# provider_supports_tools
# ============================================================

class TestProviderSupportsTools:

    @pytest.mark.unit
    def test_gemini_supports(self):
        assert provider_supports_tools("gemini") is True

    @pytest.mark.unit
    def test_groq_supports(self):
        assert provider_supports_tools("groq") is True

    @pytest.mark.unit
    def test_openrouter_supports(self):
        assert provider_supports_tools("openrouter") is True

    @pytest.mark.unit
    def test_mistral_does_not_support(self):
        assert provider_supports_tools("mistral") is False

    @pytest.mark.unit
    def test_unknown_provider(self):
        assert provider_supports_tools("unknown_xyz") is False


# ============================================================
# user_needs_tools
# ============================================================

class TestUserNeedsTools:

    @pytest.mark.unit
    @pytest.mark.parametrize("text", [
        "покажи все .py файлы",
        "покажи файлы в проекте",
        "прочитай main.py",
        "проанализируй XAUUSD",
        "сделай брифинг по золоту",
        "отправь в телеграм",
        "скинь в тг",
        "покажи котировку BTCUSD",
        "какие у меня позиции?",
        "купи 0.01 BTCUSD",
        "закрой все позиции",
        "покажи процессы",
        "сделай скриншот",
        "что на экране",
        "найди в интернете новости",
        "проанализируй с скриншотом",
        "что нового в Python",
    ])
    def test_needs_tools_positive(self, text):
        assert user_needs_tools(text) is True, f"'{text}' должен требовать tools"

    @pytest.mark.unit
    @pytest.mark.parametrize("text", [
        "привет",
        "как дела",
        "напиши функцию quicksort",
        "объясни что такое рекурсия",
        "отрефактори этот код",
        "что такое Python",
        "расскажи анекдот",
    ])
    def test_needs_tools_negative(self, text):
        assert user_needs_tools(text) is False, f"'{text}' НЕ должен требовать tools"

    @pytest.mark.unit
    def test_empty(self):
        assert user_needs_tools("") is False
        assert user_needs_tools(None) is False


# ============================================================
# pick_provider_for_category — базовые случаи
# ============================================================

class TestPickProviderBasic:

    @pytest.mark.unit
    def test_trading_goes_to_gemini(self):
        result = pick_provider_for_category("trading", "анализ XAUUSD", ALL)
        assert result == "gemini"

    @pytest.mark.unit
    def test_vision_goes_to_gemini(self):
        result = pick_provider_for_category("vision", "что на экране", ALL)
        assert result == "gemini"

    @pytest.mark.unit
    def test_web_search_goes_to_gemini(self):
        result = pick_provider_for_category("web_search", "найди в интернете", ALL)
        assert result == "gemini"

    @pytest.mark.unit
    def test_general_goes_to_groq(self):
        result = pick_provider_for_category("general", "привет", ALL)
        assert result == "groq"


# ============================================================
# pick_provider_for_category — главный кейс: code + tools
# ============================================================

class TestPickProviderCodeWithTools:

    @pytest.mark.unit
    def test_code_with_tools_goes_to_gemini(self):
        """'покажи .py файлы' — требует tools, Mistral не умеет → Gemini."""
        result = pick_provider_for_category(
            "code",
            "покажи все .py файлы в проекте",
            ALL,
        )
        assert result == "gemini", f"Ожидали gemini, получили {result}"

    @pytest.mark.unit
    def test_code_without_tools_goes_to_mistral(self):
        """'напиши функцию' — не требует tools, Mistral подходит."""
        result = pick_provider_for_category(
            "code",
            "напиши функцию quicksort",
            ALL,
        )
        assert result == "mistral"

    @pytest.mark.unit
    def test_code_with_tools_no_gemini(self):
        """Если Gemini недоступен — fallback на OpenRouter."""
        result = pick_provider_for_category(
            "code",
            "покажи все .py файлы",
            ["groq", "mistral", "openrouter"],
        )
        assert result == "openrouter"

    @pytest.mark.unit
    def test_code_with_tools_no_gemini_no_openrouter(self):
        """Если Gemini и OpenRouter недоступны — остаётся Groq."""
        result = pick_provider_for_category(
            "code",
            "покажи все .py файлы",
            ["groq", "mistral"],
        )
        assert result == "groq"

    @pytest.mark.unit
    def test_code_without_tools_no_mistral(self):
        """Если Mistral недоступен — fallback на Gemini."""
        result = pick_provider_for_category(
            "code",
            "напиши функцию",
            ["gemini", "groq"],
        )
        assert result == "gemini"


# ============================================================
# Fallback при недоступности провайдеров
# ============================================================

class TestPickProviderFallback:

    @pytest.mark.unit
    def test_trading_no_gemini(self):
        """Trading, но Gemini нет — OpenRouter."""
        result = pick_provider_for_category("trading", "анализ", ["groq", "openrouter"])
        assert result == "openrouter"

    @pytest.mark.unit
    def test_general_no_groq(self):
        """General, но Groq нет — OpenRouter."""
        result = pick_provider_for_category("general", "привет", ["gemini", "openrouter"])
        assert result == "openrouter"

    @pytest.mark.unit
    def test_unknown_category(self):
        result = pick_provider_for_category("unknown", "test", ALL)
        assert result is None

    @pytest.mark.unit
    def test_nothing_available(self):
        result = pick_provider_for_category("trading", "анализ", [])
        assert result is None


# ============================================================
# describe_capabilities
# ============================================================

class TestDescribeCapabilities:

    @pytest.mark.unit
    def test_gemini(self):
        s = describe_capabilities("gemini")
        assert "gemini" in s
        assert "tools=True" in s

    @pytest.mark.unit
    def test_mistral(self):
        s = describe_capabilities("mistral")
        assert "mistral" in s
        assert "tools=False" in s

    @pytest.mark.unit
    def test_unknown(self):
        s = describe_capabilities("unknown")
        assert "unknown" in s


# ============================================================
# Проверка реестра
# ============================================================

class TestRegistry:

    @pytest.mark.unit
    def test_all_providers_present(self):
        for p in ["gemini", "groq", "mistral", "openrouter"]:
            assert p in PROVIDER_CAPABILITIES

    @pytest.mark.unit
    def test_each_has_supports_tools(self):
        for p, caps in PROVIDER_CAPABILITIES.items():
            assert "supports_tools" in caps, f"{p} без supports_tools"