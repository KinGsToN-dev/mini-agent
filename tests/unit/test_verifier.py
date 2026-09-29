"""Тесты для agent/verifier.py."""
from unittest.mock import MagicMock, patch

import pytest

from agent.verifier import Verifier, VerifyResult


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent._tg_sent_during_ask = False
    return agent


@pytest.fixture
def verifier(mock_agent):
    return Verifier(mock_agent)


# ============================================================
# Проверка _user_wants_telegram
# ============================================================

class TestUserWantsTelegram:

    @pytest.mark.unit
    @pytest.mark.parametrize("text", [
        "отправь в телеграм",
        "отправь анализ в телеграм",
        "скинь в тг",
        "пришли в телеграм",
        "send to telegram",
    ])
    def test_positive(self, verifier, text):
        assert verifier._user_wants_telegram(text) is True

    @pytest.mark.unit
    @pytest.mark.parametrize("text", [
        "привет",
        "как дела",
        "проанализируй XAUUSD",
    ])
    def test_negative(self, verifier, text):
        assert verifier._user_wants_telegram(text) is False


# ============================================================
# Проверка _claims_sent
# ============================================================

class TestClaimsSent:

    @pytest.mark.unit
    @pytest.mark.parametrize("text", [
        "Отправлено в Telegram.",
        "Я отправил анализ.",
        "Successfully sent.",
    ])
    def test_positive(self, verifier, text):
        assert verifier._claims_sent(text) is True

    @pytest.mark.unit
    def test_negative(self, verifier):
        assert verifier._claims_sent("Вот ваш анализ.") is False


# ============================================================
# Проверка _collect_errors
# ============================================================

class TestCollectErrors:

    @pytest.mark.unit
    def test_no_errors(self, verifier):
        results = [
            {"name": "mt5_summary", "result": [{"type": "text", "text": "OK"}]},
        ]
        assert verifier._collect_errors(results) == []

    @pytest.mark.unit
    def test_with_errors(self, verifier):
        results = [
            {"name": "mt5_summary", "result": [{"type": "text", "text": "[ERROR] MT5 unavailable"}]},
        ]
        errors = verifier._collect_errors(results)
        assert len(errors) == 1
        assert "MT5 unavailable" in errors[0]

    @pytest.mark.unit
    def test_string_result(self, verifier):
        results = ["[ERROR] something failed"]
        errors = verifier._collect_errors(results)
        assert len(errors) == 1

    @pytest.mark.unit
    def test_empty(self, verifier):
        assert verifier._collect_errors([]) == []
        assert verifier._collect_errors(None) == []


# ============================================================
# check_and_fix — основная логика
# ============================================================

class TestCheckAndFix:

    @pytest.mark.unit
    def test_ok_no_issues(self, verifier):
        """Всё хорошо — issues пустой."""
        result = verifier.check_and_fix(
            user_text="проанализируй XAUUSD",
            tool_results=[],
            final_text="Анализ готов.",
            chat_id=None,
        )
        assert isinstance(result, VerifyResult)
        assert result.final_text == "Анализ готов."
        assert result.issues == []
        assert result.fixed is False

    @pytest.mark.unit
    def test_empty_response_retries(self, verifier):
        """Пустой ответ -> retry через retry_ask_fn."""
        def retry_fn(text):
            return "Новый ответ"

        result = verifier.check_and_fix(
            user_text="привет",
            tool_results=[],
            final_text="",
            chat_id=None,
            retry_ask_fn=retry_fn,
        )
        assert result.final_text == "Новый ответ"
        assert result.fixed is True
        assert "empty_response" in result.issues

    @pytest.mark.unit
    def test_tool_error_retries(self, verifier):
        """[ERROR] в tool_results -> retry."""
        def retry_fn(text):
            return "Успешный ответ после retry"

        result = verifier.check_and_fix(
            user_text="проанализируй",
            tool_results=[{"name": "mt5_summary", "result": [{"type": "text", "text": "[ERROR] MT5 unavailable"}]}],
            final_text="Что-то упало",
            chat_id=None,
            retry_ask_fn=retry_fn,
        )
        assert result.fixed is True
        assert any("tool_error" in i for i in result.issues)

    @pytest.mark.unit
    def test_missing_telegram_send_forced(self, verifier):
        """Запрос 'отправь в телеграм', telegram_send не вызван, ответ 'Отправлено' -> force-send."""
        with patch.object(verifier, "_force_telegram_send", return_value=True) as mock_force:
            result = verifier.check_and_fix(
                user_text="отправь анализ в телеграм",
                tool_results=[],
                final_text="Отправлено в Telegram.",
                chat_id=12345,
            )
            assert result.fixed is True
            assert "missing_telegram_send" in result.issues
            assert "forced_telegram_send" in result.issues
            mock_force.assert_called_once()

    @pytest.mark.unit
    def test_telegram_sent_no_force(self, verifier, mock_agent):
        """telegram_send был вызван (флаг на агенте) -> force-send НЕ нужен."""
        mock_agent._tg_sent_during_ask = True
        with patch.object(verifier, "_force_telegram_send") as mock_force:
            result = verifier.check_and_fix(
                user_text="отправь в телеграм",
                tool_results=[],
                final_text="Отправлено.",
                chat_id=12345,
            )
            assert "missing_telegram_send" not in result.issues
            mock_force.assert_not_called()

    @pytest.mark.unit
    def test_no_chat_id_no_force(self, verifier):
        """Нет chat_id (запрос не из Telegram) -> force-send НЕ нужен."""
        with patch.object(verifier, "_force_telegram_send") as mock_force:
            result = verifier.check_and_fix(
                user_text="отправь в телеграм",
                tool_results=[],
                final_text="Отправлено.",
                chat_id=None,
            )
            mock_force.assert_not_called()

    @pytest.mark.unit
    def test_force_send_replaces_text(self, verifier):
        """После force-send текст заменяется на 'Отправлено в Telegram.'"""
        with patch.object(verifier, "_force_telegram_send", return_value=True):
            result = verifier.check_and_fix(
                user_text="отправь в телеграм",
                tool_results=[],
                final_text="Отправлено!",
                chat_id=12345,
            )
            assert result.final_text == "Отправлено в Telegram."


# ============================================================
# _force_telegram_send
# ============================================================

class TestForceTelegramSend:

    @pytest.mark.unit
    def test_success(self, verifier):
        with patch("tools.telegram_tools.telegram_send", return_value="[OK]") as mock_send:
            ok = verifier._force_telegram_send("test", 12345)
            assert ok is True
            mock_send.assert_called_once()

    @pytest.mark.unit
    def test_failure(self, verifier):
        with patch("tools.telegram_tools.telegram_send", side_effect=Exception("network")):
            ok = verifier._force_telegram_send("test", 12345)
            assert ok is False
