"""Тесты для providers/openrouter.py — с моками OpenAI клиента."""
from unittest.mock import MagicMock, patch

import pytest

from providers.openrouter import OpenRouterProvider


# ============================================================
# Фикстуры
# ============================================================

@pytest.fixture
def provider():
    """Провайдер с тестовым каталогом."""
    catalog = [
        ("llama-3.3-70b", "meta-llama/llama-3.3-70b-instruct:free", "умная"),
        ("deepseek-r1", "deepseek/deepseek-r1:free", "reasoning"),
        ("qwen-72b", "qwen/qwen-2.5-72b-instruct:free", "средняя"),
    ]
    fallbacks = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
        "openrouter/free",
    ]
    with patch("providers.openrouter.OpenAI"):
        p = OpenRouterProvider(
            api_key="test-key",
            model_catalog=catalog,
            default_model="meta-llama/llama-3.3-70b-instruct:free",
            fallback_models=fallbacks,
        )
    return p


# ============================================================
# Инициализация
# ============================================================

class TestInit:

    @pytest.mark.unit
    def test_name(self, provider):
        assert provider.name == "openrouter"

    @pytest.mark.unit
    def test_supports_tools(self, provider):
        assert provider.supports_tools is True

    @pytest.mark.unit
    def test_list_models(self, provider):
        models = provider.list_models()
        assert len(models) == 3
        assert models[0][0] == "llama-3.3-70b"

    @pytest.mark.unit
    def test_default_model(self, provider):
        assert provider.default_model() == "meta-llama/llama-3.3-70b-instruct:free"


# ============================================================
# Fallback: обрезка до 3
# ============================================================

class TestFallbackTruncation:

    @pytest.mark.unit
    def test_fallback_truncated_to_3(self, provider):
        """Проверяем, что в extra_body максимум 3 модели."""
        # Мок ответа
        mock_response = MagicMock()
        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.content = "OK"
        mock_response.choices = [MagicMock(message=mock_msg)]
        provider.client.chat.completions.create.return_value = mock_response

        provider.ask(
            model_name="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": "test"}],
        )

        # Проверяем аргументы вызова
        call_kwargs = provider.client.chat.completions.create.call_args.kwargs
        extra_body = call_kwargs.get("extra_body", {})
        models_list = extra_body.get("models", [])

        assert len(models_list) <= 3, f"Должно быть ≤ 3, а есть {len(models_list)}"

    @pytest.mark.unit
    def test_model_still_present(self, provider):
        """model должен остаться в kwargs (OpenRouter требует)."""
        mock_response = MagicMock()
        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.content = "OK"
        mock_response.choices = [MagicMock(message=mock_msg)]
        provider.client.chat.completions.create.return_value = mock_response

        provider.ask(
            model_name="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": "test"}],
        )

        call_kwargs = provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("model") == "meta-llama/llama-3.3-70b-instruct:free"
        assert "extra_body" in call_kwargs


# ============================================================
# Tool-calling
# ============================================================

class TestToolCalling:

    @pytest.mark.unit
    def test_tool_call_executed(self, provider):
        """Модель вызвала инструмент → должен выполниться."""
        # Мок ответа с tool_call
        mock_tc = MagicMock()
        mock_tc.id = "call_1"
        mock_tc.function.name = "read_file"
        mock_tc.function.arguments = '{"path": "test.txt"}'

        mock_msg_1 = MagicMock()
        mock_msg_1.tool_calls = [mock_tc]
        mock_msg_1.content = ""

        # Второй ответ — обычный текст
        mock_msg_2 = MagicMock()
        mock_msg_2.tool_calls = None
        mock_msg_2.content = "Файл прочитан"

        mock_response_1 = MagicMock(choices=[MagicMock(message=mock_msg_1)])
        mock_response_2 = MagicMock(choices=[MagicMock(message=mock_msg_2)])

        provider.client.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        with patch("tools.registry.execute_tool") as mock_exec:
            mock_exec.return_value = "file content"
            result = provider.ask(
                model_name="test-model",
                messages=[{"role": "user", "content": "прочитай файл"}],
                tools=[{"type": "function", "function": {"name": "read_file"}}],
            )

        assert result == "Файл прочитан"
        mock_exec.assert_called_once_with("read_file", {"path": "test.txt"})

    @pytest.mark.unit
    def test_no_tools_no_extra_body(self):
        """Если tools не переданы, extra_body не добавляется (если model=free)."""
        with patch("providers.openrouter.OpenAI"):
            p = OpenRouterProvider(
                api_key="test",
                model_catalog=[],
                default_model="openrouter/free",
                fallback_models=["m1", "m2"],
            )

        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.content = "OK"
        mock_response = MagicMock(choices=[MagicMock(message=mock_msg)])
        p.client.chat.completions.create.return_value = mock_response

        p.ask(model_name="openrouter/free", messages=[{"role": "user", "content": "hi"}])

        call_kwargs = p.client.chat.completions.create.call_args.kwargs
        # Для openrouter/free extra_body НЕ добавляем
        assert "extra_body" not in call_kwargs


# ============================================================
# Deduplication
# ============================================================

class TestDeduplication:

    @pytest.mark.unit
    def test_duplicate_tool_calls_ignored(self, provider):
        """Два одинаковых tool_call → только один вызов."""
        mock_tc1 = MagicMock()
        mock_tc1.id = "call_1"
        mock_tc1.function.name = "read_file"
        mock_tc1.function.arguments = '{"path": "a.txt"}'

        mock_tc2 = MagicMock()
        mock_tc2.id = "call_2"  # другой id, но те же name+args
        mock_tc2.function.name = "read_file"
        mock_tc2.function.arguments = '{"path": "a.txt"}'

        mock_msg_1 = MagicMock()
        mock_msg_1.tool_calls = [mock_tc1, mock_tc2]
        mock_msg_1.content = ""

        mock_msg_2 = MagicMock()
        mock_msg_2.tool_calls = None
        mock_msg_2.content = "OK"

        mock_response_1 = MagicMock(choices=[MagicMock(message=mock_msg_1)])
        mock_response_2 = MagicMock(choices=[MagicMock(message=mock_msg_2)])

        provider.client.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        with patch("tools.registry.execute_tool") as mock_exec:
            mock_exec.return_value = "content"
            provider.ask(
                model_name="test",
                messages=[{"role": "user", "content": "x"}],
            )

        # Выполнено должно быть ровно 1 раз (дубликат отсечён)
        assert mock_exec.call_count == 1


# ============================================================
# Ошибки
# ============================================================

class TestErrors:

    @pytest.mark.unit
    def test_empty_content_returns_message(self, provider):
        mock_msg = MagicMock()
        mock_msg.tool_calls = None
        mock_msg.content = None
        mock_response = MagicMock(choices=[MagicMock(message=mock_msg)])
        provider.client.chat.completions.create.return_value = mock_response

        result = provider.ask(
            model_name="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": "x"}],
        )
        assert result == "(пустой ответ)"