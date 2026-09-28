"""Тесты для telegram_bot."""
from unittest.mock import patch

import pytest

from telegram_bot import config, handler, safety


class TestConfig:

    @pytest.mark.unit
    def test_token_missing(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_COMMAND_BOT_TOKEN", raising=False)
        with pytest.raises(RuntimeError):
            config.get_token()

    @pytest.mark.unit
    def test_token_present(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_COMMAND_BOT_TOKEN", "123:ABC")
        assert config.get_token() == "123:ABC"

    @pytest.mark.unit
    def test_allowed_chat_ids(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_COMMAND_ALLOWED_CHAT_IDS", "111,222, 333")
        assert config.get_allowed_chat_ids() == {111, 222, 333}

    @pytest.mark.unit
    def test_allowed_empty_fails(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_COMMAND_ALLOWED_CHAT_IDS", "")
        with pytest.raises(RuntimeError):
            config.get_allowed_chat_ids()

    @pytest.mark.unit
    def test_allowed_invalid_fails(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_COMMAND_ALLOWED_CHAT_IDS", "abc")
        with pytest.raises(RuntimeError):
            config.get_allowed_chat_ids()


class TestSafety:

    @pytest.mark.unit
    def test_read_allowed(self):
        assert safety.is_tool_allowed("read_file") is True
        assert safety.is_tool_allowed("mt5_summary") is True

    @pytest.mark.unit
    def test_dangerous_forbidden(self):
        assert safety.is_tool_allowed("run_shell") is False
        assert safety.is_tool_allowed("write_file") is False

    @pytest.mark.unit
    def test_filter_tools(self):
        tools = ["read_file", "run_shell", "mt5_summary"]
        assert set(safety.filter_tools(tools)) == {"read_file", "mt5_summary"}


class TestHandlerCommands:

    @pytest.mark.unit
    def test_start(self):
        r = handler.handle_message(1, "/start")
        assert "mini-agent" in r.lower() or "привет" in r.lower()

    @pytest.mark.unit
    def test_help(self):
        r = handler.handle_message(1, "/help")
        assert "/status" in r

    @pytest.mark.unit
    def test_status(self):
        with patch("telegram_bot.handler._get",
                   return_value={"provider": "gemini", "model": "x", "mode": "ask"}):
            r = handler.handle_message(1, "/status")
            assert "gemini" in r

    @pytest.mark.unit
    def test_reset(self):
        with patch("telegram_bot.handler._post", return_value={}):
            r = handler.handle_message(1, "/reset")
            assert "сброшен" in r.lower()


class TestHandlerAsk:

    @pytest.mark.unit
    def test_ask_calls_server(self):
        resp = {"answer": "Привет!", "provider": "groq", "model": "x", "duration_ms": 100}
        with patch("telegram_bot.handler._post", return_value=resp) as mock_post:
            r = handler.handle_message(999, "привет")
            assert "Привет!" in r
            payload = mock_post.call_args[0][1]
            assert payload["session_id"] == "tg_999"

    @pytest.mark.unit
    def test_ask_server_error(self):
        with patch("telegram_bot.handler._post",
                   side_effect=RuntimeError("Сервер недоступен")):
            r = handler.handle_message(1, "test")
            assert "недоступен" in r.lower()

    @pytest.mark.unit
    def test_empty_message(self):
        r = handler.handle_message(1, "")
        assert "пусто" in r.lower()


class TestSplitMessage:

    @pytest.mark.unit
    def test_short(self):
        assert handler.split_message("Hello", limit=100) == ["Hello"]

    @pytest.mark.unit
    def test_long(self):
        parts = handler.split_message("abc " * 1000, limit=500)
        assert len(parts) > 1
        for p in parts:
            assert len(p) <= 500

    @pytest.mark.unit
    def test_long_word(self):
        text = "x" * 1000
        parts = handler.split_message(text, limit=300)
        assert "".join(parts) == text


class TestSessionId:

    @pytest.mark.unit
    def test_format(self):
        assert handler.session_id_for_chat(123) == "tg_123"


class TestBotFilters:

    @pytest.mark.unit
    def test_whitelist_blocks_unknown(self):
        from telegram_bot.bot import TelegramBot
        bot = TelegramBot(token="x", allowed_chat_ids={111})
        update = {"message": {"chat": {"id": 999}, "from": {"id": 999, "is_bot": False}, "text": "hi"}}
        with patch.object(bot, "_send_message") as mock_send:
            bot._process_update(update)
            mock_send.assert_not_called()

    @pytest.mark.unit
    def test_whitelist_allows_known(self):
        from telegram_bot.bot import TelegramBot
        bot = TelegramBot(token="x", allowed_chat_ids={111})
        update = {"message": {"chat": {"id": 111}, "from": {"id": 111, "is_bot": False}, "text": "/start"}}
        with patch.object(bot, "_send_message") as mock_send:
            bot._process_update(update)
            mock_send.assert_called()

    @pytest.mark.unit
    def test_bot_messages_ignored(self):
        from telegram_bot.bot import TelegramBot
        bot = TelegramBot(token="x", allowed_chat_ids={111})
        update = {"message": {"chat": {"id": 111}, "from": {"id": 111, "is_bot": True}, "text": "/start"}}
        with patch.object(bot, "_send_message") as mock_send:
            bot._process_update(update)
            mock_send.assert_not_called()

# ============================================================
# C.5: chat_id передаётся в /ask
# ============================================================

class TestHandlerAskChatId:

    @pytest.mark.unit
    def test_ask_passes_chat_id_to_server(self):
        """handle_message передаёт chat_id в payload /ask."""
        resp = {"answer": "ok", "provider": "p", "model": "m", "duration_ms": 0}
        with patch("telegram_bot.handler._post", return_value=resp) as mock_post:
            handler.handle_message(999, "привет")
            # mock_post вызывается как _post(url, payload)
            call_args = mock_post.call_args[0]
            url = call_args[0]
            payload = call_args[1]
            assert "/ask" in url
            assert payload["chat_id"] == 999
            assert payload["text"] == "привет"
            assert payload["session_id"] == "tg_999"

    @pytest.mark.unit
    def test_ask_passes_different_chat_ids(self):
        """Разные chat_id — разные payload."""
        resp = {"answer": "ok", "provider": "p", "model": "m", "duration_ms": 0}
        for cid in [111, 22222, 638829844]:
            with patch("telegram_bot.handler._post", return_value=resp) as mock_post:
                handler.handle_message(cid, "test")
                payload = mock_post.call_args[0][1]
                assert payload["chat_id"] == cid
                assert payload["session_id"] == f"tg_{cid}"

    @pytest.mark.unit
    def test_reset_does_not_pass_chat_id(self):
        """/reset не передаёт chat_id (только session_id)."""
        with patch("telegram_bot.handler._post", return_value={}) as mock_post:
            handler.handle_message(999, "/reset")
            payload = mock_post.call_args[0][1]
            assert "chat_id" not in payload or payload.get("chat_id") is None

