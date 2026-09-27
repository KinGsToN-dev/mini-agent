"""Тесты для tools/mt5_tools.py — с моками MT5."""
from unittest.mock import MagicMock, patch

import pytest

from tools import mt5_tools


@pytest.fixture
def mock_mt5():
    """Мок MetaTrader5 модуля."""
    with patch.object(mt5_tools, "_mt5") as mock:
        mt5 = MagicMock()
        mt5.shutdown = MagicMock()
        mock.return_value = (mt5, None)
        yield mt5


class TestQuote:

    @pytest.mark.unit
    def test_quote_returns_bid_ask(self, mock_mt5):
        tick = MagicMock()
        tick.bid = 1.13904
        tick.ask = 1.13916
        tick.time = 1790380784
        mock_mt5.symbol_info_tick.return_value = tick

        info = MagicMock()
        info.digits = 5
        mock_mt5.symbol_info.return_value = info

        result = mt5_tools.mt5_quote("EURUSD")
        assert "Bid: 1.13904" in result
        assert "Ask: 1.13916" in result
        assert "EURUSD" in result

    @pytest.mark.unit
    def test_quote_symbol_not_found(self, mock_mt5):
        mock_mt5.symbol_info_tick.return_value = None
        result = mt5_tools.mt5_quote("FAKESYMBOL")
        assert "[ERROR]" in result
        assert "FAKESYMBOL" in result

    @pytest.mark.unit
    def test_quote_mt5_not_available(self):
        with patch.object(mt5_tools, "_mt5") as mock:
            mock.return_value = (None, "[ERROR] MT5 не запущен")
            result = mt5_tools.mt5_quote("EURUSD")
            assert "[ERROR]" in result


class TestBars:

    @pytest.mark.unit
    def test_bars_invalid_timeframe(self, mock_mt5):
        result = mt5_tools.mt5_bars("EURUSD", timeframe="XX")
        assert "[ERROR]" in result
        assert "timeframe" in result.lower() or "timeframe" in result

    @pytest.mark.unit
    def test_bars_no_data(self, mock_mt5):
        mock_mt5.copy_rates_from_pos.return_value = None
        # H1 существует
        mock_mt5.TIMEFRAME_H1 = "TIMEFRAME_H1"
        result = mt5_tools.mt5_bars("EURUSD", "H1", 10)
        assert "[ERROR]" in result

    @pytest.mark.unit
    def test_bars_returns_ohlc(self, mock_mt5):
        import numpy as np
        mock_mt5.TIMEFRAME_H1 = "H1"

        rates = np.array([
            (1790380000, 1.0, 1.1, 0.9, 1.05, 100, 1, 1),
            (1790383600, 1.05, 1.15, 1.0, 1.10, 200, 1, 1),
        ], dtype=[
            ("time", "i8"), ("open", "f8"), ("high", "f8"),
            ("low", "f8"), ("close", "f8"), ("tick_volume", "i8"),
            ("spread", "i4"), ("real_volume", "i8"),
        ])
        mock_mt5.copy_rates_from_pos.return_value = rates

        result = mt5_tools.mt5_bars("EURUSD", "H1", 2)
        assert "EURUSD H1" in result
        assert "open" in result
        assert "close" in result


class TestAccount:

    @pytest.mark.unit
    def test_account_returns_info(self, mock_mt5):
        acc = MagicMock()
        acc.login = 12345
        acc.server = "TestServer"
        acc.currency = "USD"
        acc.balance = 10000.0
        acc.equity = 10500.0
        acc.margin = 500.0
        acc.margin_free = 10000.0
        acc.margin_level = 2100.0
        acc.profit = 500.0
        mock_mt5.account_info.return_value = acc

        result = mt5_tools.mt5_account()
        assert "12345" in result
        assert "10000.00" in result
        assert "USD" in result

    @pytest.mark.unit
    def test_account_not_connected(self, mock_mt5):
        mock_mt5.account_info.return_value = None
        result = mt5_tools.mt5_account()
        assert "[ERROR]" in result


class TestPositions:

    @pytest.mark.unit
    def test_positions_empty(self, mock_mt5):
        mock_mt5.positions_get.return_value = []
        result = mt5_tools.mt5_positions()
        assert "нет" in result.lower() or "0" in result

    @pytest.mark.unit
    def test_positions_with_data(self, mock_mt5):
        p = MagicMock()
        p.ticket = 12345
        p.symbol = "EURUSD"
        p.type = 0  # BUY
        p.volume = 0.1
        p.price_open = 1.1400
        p.price_current = 1.1410
        p.profit = 10.0
        mock_mt5.positions_get.return_value = [p]

        result = mt5_tools.mt5_positions()
        assert "EURUSD" in result
        assert "BUY" in result
        assert "10.00" in result or "+10" in result