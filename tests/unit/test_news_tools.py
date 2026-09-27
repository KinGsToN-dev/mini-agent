"""Тесты для tools/news_tools.py — с моками Biquote.
Пропускаются, если biquote не установлен.
"""
from unittest.mock import MagicMock, patch

import pytest

# Пропускаем весь файл, если biquote не установлен
pytest.importorskip("biquote", reason="biquote not installed")

from tools import news_tools


@pytest.fixture
def mock_events():
    """Набор тестовых событий."""
    return [
        {
            "time": "2026-09-28T13:30:00Z",
            "countryCode": "US",
            "currency": "USD",
            "name": "Non-Farm Payrolls",
            "importance": "high",
            "forecast": 180,
            "previous": 175,
            "actual": None,
        },
        {
            "time": "2026-09-28T14:00:00Z",
            "countryCode": "EU",
            "currency": "EUR",
            "name": "ECB Interest Rate Decision",
            "importance": "high",
            "forecast": 4.25,
            "previous": 4.25,
            "actual": None,
        },
        {
            "time": "2026-09-28T10:00:00Z",
            "countryCode": "US",
            "currency": "USD",
            "name": "Minor Speech",
            "importance": "low",
            "forecast": None,
            "previous": None,
            "actual": None,
        },
    ]


class TestEconCalendar:

    @pytest.mark.unit
    def test_biquote_not_installed(self):
        with patch.dict("sys.modules", {"biquote": None}):
            result = news_tools.econ_calendar()
            # Может вернуть ошибку установки или другое
            assert isinstance(result, str)

    @pytest.mark.unit
    def test_filter_by_country(self, mock_events):
        with patch("biquote.Biquote") as MockBQ:
            MockBQ.return_value.calendar.return_value = mock_events
            result = news_tools.econ_calendar(countries="US", importance="high")
            assert "Non-Farm Payrolls" in result
            assert "ECB" not in result

    @pytest.mark.unit
    def test_filter_by_importance(self, mock_events):
        with patch("biquote.Biquote") as MockBQ:
            MockBQ.return_value.calendar.return_value = mock_events
            result = news_tools.econ_calendar(countries="US", importance="high")
            assert "Minor Speech" not in result

    @pytest.mark.unit
    def test_empty_events(self):
        with patch("biquote.Biquote") as MockBQ:
            MockBQ.return_value.calendar.return_value = []
            result = news_tools.econ_calendar()
            assert "нет" in result.lower() or "No" in result

    @pytest.mark.unit
    def test_forecast_in_output(self, mock_events):
        with patch("biquote.Biquote") as MockBQ:
            MockBQ.return_value.calendar.return_value = mock_events
            result = news_tools.econ_calendar(countries="US", importance="high")
            assert "прогноз" in result.lower() or "forecast" in result.lower()


class TestImportanceLevels:

    @pytest.mark.unit
    def test_levels_order(self):
        assert news_tools.IMPORTANCE_LEVELS["high"] > news_tools.IMPORTANCE_LEVELS["medium"]
        assert news_tools.IMPORTANCE_LEVELS["medium"] > news_tools.IMPORTANCE_LEVELS["low"]
        assert news_tools.IMPORTANCE_LEVELS["low"] > news_tools.IMPORTANCE_LEVELS["none"]