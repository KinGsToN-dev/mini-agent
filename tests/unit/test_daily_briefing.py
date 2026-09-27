"""Тесты для scripts/daily_briefing.py."""
from unittest.mock import MagicMock, patch

import pytest

from scripts import daily_briefing


# ============================================================
# collect_data
# ============================================================

class TestCollectData:

    @pytest.mark.unit
    def test_collects_symbols(self):
        with patch("scripts.daily_briefing.mt5_summary", return_value="BTCUSD data"), \
             patch("scripts.daily_briefing.econ_calendar", return_value="calendar data"):
            data = daily_briefing.collect_data()

        assert "BTCUSD" in data
        assert "XAUUSD" in data
        assert "EURUSD" in data
        assert "calendar data" in data

    @pytest.mark.unit
    def test_handles_mt5_error(self):
        with patch("scripts.daily_briefing.mt5_summary",
                   side_effect=Exception("MT5 not running")), \
             patch("scripts.daily_briefing.econ_calendar", return_value="cal"):
            data = daily_briefing.collect_data()
        # Не падает, включает error
        assert "ERROR" in data or "MT5" in data


# ============================================================
# log
# ============================================================

class TestLog:

    @pytest.mark.unit
    def test_log_creates_file(self, tmp_path, monkeypatch):
        log_file = tmp_path / "test.log"
        monkeypatch.setattr(daily_briefing, "LOG_FILE", log_file)

        daily_briefing.log("test message")

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "test message" in content

    @pytest.mark.unit
    def test_log_appends(self, tmp_path, monkeypatch):
        log_file = tmp_path / "test.log"
        monkeypatch.setattr(daily_briefing, "LOG_FILE", log_file)

        daily_briefing.log("first")
        daily_briefing.log("second")

        content = log_file.read_text(encoding="utf-8")
        assert "first" in content
        assert "second" in content


# ============================================================
# analyze_with_groq
# ============================================================

class TestAnalyzeWithGroq:

    @pytest.mark.unit
    def test_analyze_calls_provider(self):
        mock_provider = MagicMock()
        mock_provider.ask.return_value = "анализ текста"

        with patch("providers.registry.get_provider", return_value=mock_provider):
            result = daily_briefing.analyze_with_groq("test data", mode="daily")

        assert result == "анализ текста"
        mock_provider.ask.assert_called_once()

    @pytest.mark.unit
    def test_analyze_handles_error(self):
        with patch("providers.registry.get_provider",
                   side_effect=Exception("No Groq")):
            result = daily_briefing.analyze_with_groq("test data", mode="daily")
        # Не падает — возвращает error + data
        assert "ERROR" in result or "test data" in result