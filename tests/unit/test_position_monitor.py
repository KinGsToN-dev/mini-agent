"""Тесты для scripts/position_monitor.py."""
import json
from unittest.mock import MagicMock, patch

import pytest

from scripts import position_monitor


# ============================================================
# State management
# ============================================================

class TestState:

    @pytest.mark.unit
    def test_load_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(position_monitor, "STATE_FILE", tmp_path / "state.json")
        assert position_monitor.load_state() == {}

    @pytest.mark.unit
    def test_save_and_load(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(position_monitor, "STATE_FILE", state_file)

        position_monitor.save_state({"total_profit": 1.5, "count": 2})
        loaded = position_monitor.load_state()

        assert loaded["total_profit"] == 1.5
        assert loaded["count"] == 2

    @pytest.mark.unit
    def test_load_corrupt_returns_empty(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text("invalid json {{{", encoding="utf-8")
        monkeypatch.setattr(position_monitor, "STATE_FILE", state_file)
        assert position_monitor.load_state() == {}


# ============================================================
# parse_positions
# ============================================================

class TestParsePositions:

    @pytest.mark.unit
    def test_mt5_not_running(self):
        with patch("scripts.position_monitor.mt5", create=True) as mock_mt5, \
             patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
            mock_mt5.initialize.return_value = False
            positions, total, status = position_monitor.parse_positions()
        assert positions == []
        assert "MT5 не запущен" in status or "не запущен" in status

    @pytest.mark.unit
    def test_no_positions(self):
        with patch("scripts.position_monitor.mt5", create=True) as mock_mt5, \
             patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
            mock_mt5.initialize.return_value = True
            mock_mt5.positions_get.return_value = None
            mock_mt5.shutdown = MagicMock()
            positions, total, status = position_monitor.parse_positions()
        assert positions == []
        assert total == 0

    @pytest.mark.unit
    def test_with_positions(self):
        pos = MagicMock()
        pos.ticket = 12345
        pos.symbol = "BTCUSD"
        pos.type = 0  # BUY
        pos.volume = 0.01
        pos.price_open = 84000
        pos.price_current = 84500
        pos.profit = 5.0

        with patch("scripts.position_monitor.mt5", create=True) as mock_mt5, \
             patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
            mock_mt5.initialize.return_value = True
            mock_mt5.positions_get.return_value = [pos]
            mock_mt5.shutdown = MagicMock()
            positions, total, status = position_monitor.parse_positions()

        assert len(positions) == 1
        assert positions[0]["symbol"] == "BTCUSD"
        assert positions[0]["side"] == "BUY"
        assert total == 5.0


# ============================================================
# format_report
# ============================================================

class TestFormatReport:

    @pytest.mark.unit
    def test_report_contains_symbol(self):
        positions = [{
            "ticket": 123, "symbol": "BTCUSD", "side": "BUY",
            "volume": 0.01, "open": 84000, "current": 84500, "profit": 5.0,
        }]
        with patch("scripts.position_monitor.mt5_account", return_value="Баланс: $10000"):
            report = position_monitor.format_report(positions, 5.0)
        assert "BTCUSD" in report
        assert "BUY" in report
        assert "+5.00" in report or "5.00" in report
        assert "МОНИТОРИНГ" in report

    @pytest.mark.unit
    def test_report_negative_profit(self):
        positions = [{
            "ticket": 123, "symbol": "BTCUSD", "side": "SELL",
            "volume": 0.01, "open": 84000, "current": 84500, "profit": -5.0,
        }]
        with patch("scripts.position_monitor.mt5_account", return_value=""):
            report = position_monitor.format_report(positions, -5.0)
        assert "-5.00" in report
        assert "SELL" in report


# ============================================================
# Логика main
# ============================================================

class TestMainLogic:

    @pytest.mark.unit
    def test_no_positions_no_send(self):
        """Если позиций нет — ничего не отправляем."""
        with patch("scripts.position_monitor.parse_positions",
                   return_value=([], 0, "Нет позиций")), \
             patch("scripts.position_monitor.telegram_send") as mock_send, \
             patch("scripts.position_monitor.log"):
            position_monitor.main()
        mock_send.assert_not_called()

    @pytest.mark.unit
    def test_same_profit_no_send(self, tmp_path, monkeypatch):
        """Если P&L не изменился — не отправляем повторно."""
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(position_monitor, "STATE_FILE", state_file)
        state_file.write_text(json.dumps({"total_profit": 5.0, "count": 1}))

        positions = [{"symbol": "BTCUSD", "side": "BUY", "volume": 0.01,
                      "open": 84000, "current": 84500, "profit": 5.0, "ticket": 1}]

        with patch("scripts.position_monitor.parse_positions",
                   return_value=(positions, 5.0, "OK")), \
             patch("scripts.position_monitor.telegram_send") as mock_send, \
             patch("scripts.position_monitor.log"):
            position_monitor.main()
        mock_send.assert_not_called()

    @pytest.mark.unit
    def test_changed_profit_sends(self, tmp_path, monkeypatch):
        """Если P&L изменился — отправляем."""
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(position_monitor, "STATE_FILE", state_file)
        state_file.write_text(json.dumps({"total_profit": 5.0, "count": 1}))

        positions = [{"symbol": "BTCUSD", "side": "BUY", "volume": 0.01,
                      "open": 84000, "current": 84500, "profit": 10.0, "ticket": 1}]

        with patch("scripts.position_monitor.parse_positions",
                   return_value=(positions, 10.0, "OK")), \
             patch("scripts.position_monitor.telegram_send") as mock_send, \
             patch("scripts.position_monitor.mt5_account", return_value=""), \
             patch("scripts.position_monitor.log"):
            mock_send.return_value = "[OK]"
            position_monitor.main()

        mock_send.assert_called_once()