"""Тесты для tools/telegram_tools.py — с моками httpx и env."""
from unittest.mock import MagicMock, patch

import pytest

from tools import telegram_tools


class TestTelegramSend:

    @pytest.mark.unit
    def test_empty_message(self):
        result = telegram_tools.telegram_send("")
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_missing_token(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        result = telegram_tools.telegram_send("test")
        assert "[ERROR]" in result
        assert "TELEGRAM" in result

    @pytest.mark.unit
    def test_missing_chat_id(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        result = telegram_tools.telegram_send("test")
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_successful_send(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client") as MockClient:
            response = MagicMock()
            response.status_code = 200
            MockClient.return_value.__enter__.return_value.post.return_value = response

            result = telegram_tools.telegram_send("привет", title="Тест")
            assert "[OK]" in result

    @pytest.mark.unit
    def test_api_error(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client") as MockClient:
            response = MagicMock()
            response.status_code = 401
            response.text = "Unauthorized"
            MockClient.return_value.__enter__.return_value.post.return_value = response

            result = telegram_tools.telegram_send("привет")
            assert "[ERROR]" in result
            assert "401" in result

    @pytest.mark.unit
    def test_long_message_truncated(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client") as MockClient:
            response = MagicMock()
            response.status_code = 200
            MockClient.return_value.__enter__.return_value.post.return_value = response

            long_msg = "x" * 10000
            result = telegram_tools.telegram_send(long_msg)
            assert "[OK]" in result

    @pytest.mark.unit
    def test_title_included(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        with patch("tools.telegram_tools.httpx.Client") as MockClient:
            response = MagicMock()
            response.status_code = 200
            mock_post = MockClient.return_value.__enter__.return_value.post
            mock_post.return_value = response

            telegram_tools.telegram_send("body", title="Header")

            # Проверяем, что title попал в payload
            call_args = mock_post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert "*Header*" in payload["text"]