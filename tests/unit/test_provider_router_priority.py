"""Тесты приоритетов роутера провайдеров — трейдинг идёт в groq первым."""
import pytest

from agent.provider_router import pick_provider, describe_decision


ALL = ["gemini", "groq", "mistral", "openrouter"]


class TestTradingPriority:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "дай анализ по золоту и отправь в телеграмм",
        "анализ по XAUUSD",
        "сделай брифинг по BTCUSD",
        "что с ценой золота",
        "отправь анализ золота в телеграм",
        "купи 0.01 BTCUSD",
        "закрой все позиции",
    ])
    def test_trading_goes_to_groq(self, query):
        assert pick_provider(query, ALL) == "groq", \
            f"'{query}' должен идти в groq"

    @pytest.mark.unit
    def test_describe_trading(self):
        assert describe_decision("анализ по золоту") == "трейдинг"


class TestVisionPriority:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "что на экране",
        "сделай скриншот",
        "прочитай ошибку на экране",
    ])
    def test_vision_goes_to_gemini(self, query):
        """Vision — только Gemini (Groq не умеет картинки)."""
        assert pick_provider(query, ALL) == "gemini"

    @pytest.mark.unit
    def test_vision_without_gemini(self):
        """Если Gemini нет — vision не идёт никуда."""
        assert pick_provider("что на экране", ["groq", "mistral"]) is None


class TestCodePriority:

    @pytest.mark.unit
    def test_code_goes_to_mistral(self):
        assert pick_provider("напиши функцию quicksort", ALL) == "mistral"

    @pytest.mark.unit
    def test_code_without_mistral(self):
        assert pick_provider("напиши функцию", ["gemini", "groq"]) == "groq"
