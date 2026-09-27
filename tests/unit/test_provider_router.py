"""Тесты для agent/provider_router.py — выбор провайдера под задачу."""
import pytest

from agent.provider_router import pick_provider, describe_decision


ALL_PROVIDERS = ["gemini", "groq", "mistral"]


class TestVisionRouting:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "что на экране?",
        "посмотри что тут",
        "покажи что в окне",
        "сделай скриншот",
        "прочитай ошибку на экране",
        "опиши это окно",
        "screenshot please",
        "what's on the screen",
    ])
    def test_vision_to_gemini(self, query):
        assert pick_provider(query, ALL_PROVIDERS) == "gemini"

    @pytest.mark.unit
    def test_vision_describe(self):
        assert describe_decision("что на экране") == "vision"


class TestCodeRouting:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "напиши функцию сортировки",
        "создай класс User",
        "сгенерируй скрипт на Python",
        "реализуй quicksort",
        "напиши код для парсинга JSON",
        "напиши функцию на JavaScript",
        "реализуй алгоритм Дейкстры",
        "отрефактори этот код",
    ])
    def test_code_to_mistral(self, query):
        assert pick_provider(query, ALL_PROVIDERS) == "mistral"

    @pytest.mark.unit
    def test_code_describe(self):
        assert describe_decision("напиши функцию") == "код"


class TestWebSearchRouting:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "найди в интернете python 3.13",
        "поищи новости про OpenAI",
        "загугли последние события",
        "что нового в Python 3.13",
        "последние новости про AI",
        "актуальная информация про httpx",
        "search web for python tips",
    ])
    def test_web_search_to_gemini(self, query):
        assert pick_provider(query, ALL_PROVIDERS) == "gemini"

    @pytest.mark.unit
    def test_web_search_describe(self):
        assert describe_decision("найди в интернете X") == "web_search"


class TestAnalysisRouting:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "проанализируй этот код",
        "объясни почему это работает",
        "сравни два подхода",
        "исследуй эту проблему",
    ])
    def test_analysis_to_gemini(self, query):
        assert pick_provider(query, ALL_PROVIDERS) == "gemini"


class TestGeneralRouting:

    @pytest.mark.unit
    @pytest.mark.parametrize("query", [
        "привет",
        "как дела?",
        "сколько времени",
        "что ты умеешь",
        "спасибо",
    ])
    def test_general_to_groq(self, query):
        assert pick_provider(query, ALL_PROVIDERS) == "groq"

    @pytest.mark.unit
    def test_general_describe(self):
        assert describe_decision("привет") == "общее"


class TestFallback:

    @pytest.mark.unit
    def test_vision_no_gemini(self):
        assert pick_provider("что на экране", ["groq", "mistral"]) is None

    @pytest.mark.unit
    def test_code_no_mistral(self):
        assert pick_provider("напиши функцию", ["gemini", "groq"]) == "groq"

    @pytest.mark.unit
    def test_web_search_no_gemini(self):
        assert pick_provider("найди в интернете", ["groq", "mistral"]) == "groq"

    @pytest.mark.unit
    def test_nothing_available(self):
        assert pick_provider("привет", []) is None