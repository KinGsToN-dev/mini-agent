"""Тесты для tools/telegram_tools.py — новая версия с chat_id и use_command_bot."""
from unittest.mock import MagicMock, patch

import pytest

from tools import telegram_tools


def _mock_httpx(status=200, text="ok"):
    """Возвращает мок httpx.Client, имитирующий успешный ответ."""
    mock_client = MagicMock()
    response = MagicMock()
    response.status_code = status
    response.text = text
    mock_client.__enter__.return_value.post.return_value = response
    return mock_client


# ============================================================
# Базовая отправка
# ============================================================

class TestBasicSend:

    @pytest.mark.unit
    def test_empty_message(self):
        result = telegram_tools.telegram_send("")
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_missing_tokens(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        result = telegram_tools.telegram_send("test")
        assert "[ERROR]" in result
        assert "TELEGRAM_BOT_TOKEN" in result

    @pytest.mark.unit
    def test_successful_send(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send("привет", title="Тест")
            assert "[OK]" in result


# ============================================================
# Новое: chat_id
# ============================================================

class TestChatId:

    @pytest.mark.unit
    def test_chat_id_from_param(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        # TELEGRAM_CHAT_ID не задаём — должен использоваться chat_id
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        mock_client = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            result = telegram_tools.telegram_send("test", chat_id=555)
            assert "[OK]" in result

        # Проверяем payload
        post_call = mock_client.__enter__.return_value.post.call_args
        payload = post_call.kwargs.get("json") or post_call[1].get("json")
        assert payload["chat_id"] == 555

    @pytest.mark.unit
    def test_chat_id_param_overrides_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        mock_client = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            telegram_tools.telegram_send("test", chat_id=777)

        post_call = mock_client.__enter__.return_value.post.call_args
        payload = post_call.kwargs.get("json") or post_call[1].get("json")
        assert payload["chat_id"] == 777  # param важнее env


# ============================================================
# Новое: use_command_bot
# ============================================================

class TestUseCommandBot:

    @pytest.mark.unit
    def test_command_bot_token_used(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "old:TOKEN")
        monkeypatch.setenv("TELEGRAM_COMMAND_BOT_TOKEN", "new:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        mock_client = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            telegram_tools.telegram_send("test", use_command_bot=True)

        # Проверяем URL — какой токен использован
        post_call = mock_client.__enter__.return_value.post.call_args
        url = post_call[0][0] if post_call[0] else post_call.kwargs.get("url")
        assert "new:TOKEN" in url

    @pytest.mark.unit
    def test_command_bot_missing_token(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "old:TOKEN")
        monkeypatch.delenv("TELEGRAM_COMMAND_BOT_TOKEN", raising=False)

        result = telegram_tools.telegram_send("test", use_command_bot=True)
        assert "[ERROR]" in result
        assert "TELEGRAM_COMMAND_BOT_TOKEN" in result

    @pytest.mark.unit
    def test_default_uses_old_token(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "old:TOKEN")
        monkeypatch.setenv("TELEGRAM_COMMAND_BOT_TOKEN", "new:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        mock_client = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            telegram_tools.telegram_send("test")  # без use_command_bot

        post_call = mock_client.__enter__.return_value.post.call_args
        url = post_call[0][0] if post_call[0] else post_call.kwargs.get("url")
        assert "old:TOKEN" in url


# ============================================================
# Комбинация: chat_id + use_command_bot
# ============================================================

class TestCombined:

    @pytest.mark.unit
    def test_chat_id_and_command_bot(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "old:TOKEN")
        monkeypatch.setenv("TELEGRAM_COMMAND_BOT_TOKEN", "new:TOKEN")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        mock_client = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            result = telegram_tools.telegram_send(
                "test",
                chat_id=12345,
                use_command_bot=True,
            )
            assert "[OK]" in result

        post_call = mock_client.__enter__.return_value.post.call_args
        url = post_call[0][0] if post_call[0] else post_call.kwargs.get("url")
        payload = post_call.kwargs.get("json") or post_call[1].get("json")
        assert "new:TOKEN" in url
        assert payload["chat_id"] == 12345


# ============================================================
# HTML / Markdown
# ============================================================

class TestFormat:

    @pytest.mark.unit
    def test_html_detected(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send("<b>Test</b>")
            assert "HTML" in result

    @pytest.mark.unit
    def test_markdown_default(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send("*Test*")
            assert "Markdown" in result
