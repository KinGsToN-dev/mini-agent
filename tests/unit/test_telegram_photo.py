"""Тесты для telegram_send_photo."""
from unittest.mock import MagicMock, patch

import pytest

from tools import telegram_tools


def _mock_httpx(status=200, text="ok"):
    mock_client = MagicMock()
    response = MagicMock()
    response.status_code = status
    response.text = text
    mock_client.__enter__.return_value.post.return_value = response
    return mock_client


class TestPhotoValidation:

    @pytest.mark.unit
    def test_file_not_found(self, tmp_path):
        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send_photo(str(tmp_path / "missing.png"))
            assert "[ERROR]" in result
            assert "не найден" in result.lower()

    @pytest.mark.unit
    def test_photo_too_large(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        big = tmp_path / "big.png"
        big.write_bytes(b"x" * (11 * 1024 * 1024))  # 11 MB

        result = telegram_tools.telegram_send_photo(str(big))
        assert "[ERROR]" in result
        assert "большой" in result.lower() or "10 MB" in result


class TestPhotoSend:

    @pytest.mark.unit
    def test_successful_send(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG" + b"x" * 10000)

        with patch("tools.telegram_tools.httpx.Client", return_value=_mock_httpx()):
            result = telegram_tools.telegram_send_photo(str(img))
            assert "[OK]" in result

    @pytest.mark.unit
    def test_missing_token(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        img = tmp_path / "test.png"
        img.write_bytes(b"x" * 10000)

        result = telegram_tools.telegram_send_photo(str(img))
        assert "[ERROR]" in result
        assert "TELEGRAM_BOT_TOKEN" in result

    @pytest.mark.unit
    def test_command_bot_token(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "old:TOKEN")
        monkeypatch.setenv("TELEGRAM_COMMAND_BOT_TOKEN", "new:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        img = tmp_path / "test.png"
        img.write_bytes(b"x" * 10000)

        mock = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock):
            telegram_tools.telegram_send_photo(str(img), use_command_bot=True)

        # Проверяем URL
        post_call = mock.__enter__.return_value.post.call_args
        url = post_call[0][0] if post_call[0] else post_call.kwargs.get("url")
        assert "new:TOKEN" in url

    @pytest.mark.unit
    def test_chat_id_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        img = tmp_path / "test.png"
        img.write_bytes(b"x" * 10000)

        mock = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock):
            result = telegram_tools.telegram_send_photo(str(img), chat_id=555)
            assert "[OK]" in result

        post_call = mock.__enter__.return_value.post.call_args
        data = post_call.kwargs.get("data") or post_call[1].get("data")
        assert data["chat_id"] == "555"

    @pytest.mark.unit
    def test_caption_sent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        img = tmp_path / "test.png"
        img.write_bytes(b"x" * 10000)

        mock = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock):
            telegram_tools.telegram_send_photo(str(img), caption="XAUUSD (gemini)")

        post_call = mock.__enter__.return_value.post.call_args
        data = post_call.kwargs.get("data") or post_call[1].get("data")
        assert "XAUUSD" in data.get("caption", "")

    @pytest.mark.unit
    def test_caption_truncated(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        img = tmp_path / "test.png"
        img.write_bytes(b"x" * 10000)

        long_caption = "x" * 2000

        mock = _mock_httpx()
        with patch("tools.telegram_tools.httpx.Client", return_value=mock):
            telegram_tools.telegram_send_photo(str(img), caption=long_caption)

        post_call = mock.__enter__.return_value.post.call_args
        data = post_call.kwargs.get("data") or post_call[1].get("data")
        assert len(data["caption"]) <= 1003  # 1000 + "..."

    @pytest.mark.unit
    def test_telegram_400(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")

        img = tmp_path / "test.png"
        img.write_bytes(b"x" * 10000)

        with patch("tools.telegram_tools.httpx.Client",
                   return_value=_mock_httpx(400, "Bad Request")):
            result = telegram_tools.telegram_send_photo(str(img))
            assert "[ERROR]" in result
            assert "400" in result


class TestTradingViewHelpers:

    @pytest.mark.unit
    def test_get_last_screenshot_initial(self):
        from tools import tradingview
        tradingview._last_screenshot_path = None
        assert tradingview.get_last_screenshot_path() is None

    @pytest.mark.unit
    def test_get_last_vision_model_initial(self):
        from tools import tradingview
        tradingview._last_vision_model = None
        assert tradingview.get_last_vision_model() is None

    @pytest.mark.unit
    def test_set_and_get(self):
        from tools import tradingview
        tradingview._last_screenshot_path = "test.png"
        tradingview._last_vision_model = "gemini-3.5-flash-lite"
        assert tradingview.get_last_screenshot_path() == "test.png"
        assert tradingview.get_last_vision_model() == "gemini-3.5-flash-lite"
        # Сброс
        tradingview._last_screenshot_path = None
        tradingview._last_vision_model = None
