"""Тесты для tools/tradingview.py — с моками CDP и Gemini."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools import tradingview


class TestTvScreenshot:

    @pytest.mark.unit
    def test_cdp_unavailable(self):
        """CDP не отвечает → понятная ошибка."""
        with patch("tools.tradingview.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("connection refused")
            )
            result = tradingview.tv_screenshot()
            assert "[ERROR]" in result
            assert "CDP" in result or "9222" in result or "start_tradingview" in result

    @pytest.mark.unit
    def test_no_tv_tab(self):
        """CDP работает, но вкладки TradingView нет."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"type": "page", "url": "about:blank"},
        ]

        with patch("tools.tradingview.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_resp
            )
            result = tradingview.tv_screenshot()
            assert "[ERROR]" in result
            assert "не найдена" in result.lower() or "TradingView" in result

    @pytest.mark.unit
    def test_screenshot_small_file_warns(self):
        """Маленький скриншот → WARN про свёрнутое окно."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"type": "page", "url": "https://tradingview.com/chart/abc",
             "webSocketDebuggerUrl": "ws://test"},
        ]

        with patch("tools.tradingview.httpx.AsyncClient") as mock_client, \
             patch("tools.tradingview._capture_screenshot") as mock_cap:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_resp
            )
            mock_cap.return_value = b"x" * 100  # маленький

            # _capture_screenshot — async, но в tv_screenshot вызывается через asyncio.run
            # подменим через прямой вызов
            with patch("tools.tradingview._get_tv_tab", new_callable=AsyncMock) as mock_tab:
                mock_tab.return_value = {"webSocketDebuggerUrl": "ws://test"}
                with patch("tools.tradingview._capture_screenshot", new_callable=AsyncMock) as mock_c:
                    mock_c.return_value = b"x" * 100
                    result = tradingview.tv_screenshot()
                    assert "[WARN]" in result or "маленький" in result.lower()


class TestTvAnalyze:

    @pytest.mark.unit
    def test_analyze_screenshot_fail(self):
        """Если скриншот не получился — вернуть ошибку."""
        with patch("tools.tradingview.tv_screenshot", return_value="[ERROR] no CDP"):
            result = tradingview.tv_analyze("test")
            assert "[ERROR]" in result

    @pytest.mark.unit
    def test_analyze_no_api_key(self, monkeypatch, tmp_path):
        """Нет GEMINI_API_KEY → понятная ошибка."""
        from pathlib import Path

        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        fake_png = tmp_path / "test.png"
        fake_png.write_bytes(b"\x89PNG" + b"x" * 10000)

        def mock_screenshot(save_path=None):
            if save_path:
                p = Path(save_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(fake_png.read_bytes())
            return f"[OK] {save_path}"

        with patch("tools.tradingview.tv_screenshot", side_effect=mock_screenshot):
            result = tradingview.tv_analyze("test")
            assert "[ERROR]" in result
            assert "GEMINI_API_KEY" in result


class TestConfig:

    @pytest.mark.unit
    def test_cdp_url(self):
        assert "9222" in tradingview.CDP_URL

    @pytest.mark.unit
    def test_vision_models(self):
        assert len(tradingview.VISION_MODELS) > 0
        for m in tradingview.VISION_MODELS:
            assert "gemini" in m
