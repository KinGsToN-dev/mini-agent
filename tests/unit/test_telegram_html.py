"""Тесты для tools/telegram_tools.py — авто-детект HTML vs Markdown."""
from unittest.mock import MagicMock, patch

import pytest

from tools import telegram_tools


def _mock_httpx(status=200, text="ok"):
    """Возвращает мок httpx.Client."""
    mock_client = MagicMock()
    response = MagicMock()
    response.status_code = status
    response.text = text
    mock_client.__enter__.return_value.post.return_value = response
    return mock_client


class TestTelegramFormatDetection:

    @pytest.mark.unit
    def test_html_detected(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send("<b>Жирный</b> текст", title="T")

        assert "[OK]" in result
        assert "HTML" in result

    @pytest.mark.unit
    def test_markdown_default(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send("*Жирный* текст", title="T")

        assert "[OK]" in result
        assert "Markdown" in result

    @pytest.mark.unit
    def test_html_with_title(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        mock_client = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            telegram_tools.telegram_send("<i>test</i>", title="Заголовок")

        post_call = mock_client.__enter__.return_value.post.call_args
        payload = post_call.kwargs.get("json") or post_call[1].get("json")
        assert payload["parse_mode"] == "HTML"
        assert "<b>Заголовок</b>" in payload["text"]

    @pytest.mark.unit
    def test_fallback_on_400(self, monkeypatch):
        """Если Telegram отверг разметку — пробуем без неё."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        mock_client = MagicMock()
        resp_400 = MagicMock(status_code=400, text="Bad Request")
        resp_200 = MagicMock(status_code=200, text="ok")
        mock_client.__enter__.return_value.post.side_effect = [resp_400, resp_200]

        with patch("tools.telegram_tools.httpx.Client", return_value=mock_client):
            result = telegram_tools.telegram_send("<b>test</b>")

        assert "[OK]" in result
        assert "без разметки" in result

    @pytest.mark.unit
    def test_empty_message(self):
        result = telegram_tools.telegram_send("")
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_missing_env(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        result = telegram_tools.telegram_send("test")
        assert "[ERROR]" in result
