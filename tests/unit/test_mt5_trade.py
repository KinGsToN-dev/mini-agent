"""Тесты для tools/mt5_trade.py — БЕЗ реальных вызовов MT5."""
from unittest.mock import MagicMock, patch
import pytest

from tools import mt5_trade


@pytest.fixture(autouse=True)
def reset_config(tmp_path, monkeypatch):
    """Сбрасываем конфиг перед каждым тестом."""
    monkeypatch.setattr(mt5_trade, "CONFIG_FILE", tmp_path / "trade_config.json")
    monkeypatch.setattr(mt5_trade, "TRADES_LOG", tmp_path / "trades.log")
    mt5_trade.MAX_LOT = 0.1
    mt5_trade.ALLOW_LIVE = False
    mt5_trade.CONFIRM_REQUIRED = True
    mt5_trade._confirm_callback = None


# ============================================================
# Проверка объёма
# ============================================================

class TestVolumeCheck:

    @pytest.mark.unit
    def test_volume_exceeds_max_lot(self):
        """Объём больше MAX_LOT — блокируется."""
        mt5 = MagicMock()
        info = MagicMock()
        info.volume_min = 0.01
        info.volume_max = 100.0
        info.volume_step = 0.01
        mt5.symbol_info.return_value = info

        mt5_trade.MAX_LOT = 0.1
        err = mt5_trade._check_volume(mt5, "BTCUSD", 0.5)
        assert err is not None
        assert "[BLOCKED]" in err
        assert "0.5" in err and "0.1" in err

    @pytest.mark.unit
    def test_volume_below_min(self):
        mt5 = MagicMock()
        info = MagicMock()
        info.volume_min = 0.01
        info.volume_max = 100.0
        info.volume_step = 0.01
        mt5.symbol_info.return_value = info

        err = mt5_trade._check_volume(mt5, "BTCUSD", 0.001)
        assert err is not None
        assert "[ERROR]" in err

    @pytest.mark.unit
    def test_volume_ok(self):
        mt5 = MagicMock()
        info = MagicMock()
        info.volume_min = 0.01
        info.volume_max = 100.0
        info.volume_step = 0.01
        mt5.symbol_info.return_value = info

        err = mt5_trade._check_volume(mt5, "BTCUSD", 0.05)
        assert err is None


# ============================================================
# Проверка аккаунта
# ============================================================

class TestAccountCheck:

    @pytest.mark.unit
    def test_demo_ok(self):
        mt5 = MagicMock()
        acc = MagicMock()
        acc.trade_mode = 0  # DEMO
        acc.login = 12345
        mt5.account_info.return_value = acc

        mt5_trade.ALLOW_LIVE = False
        err = mt5_trade._check_account(mt5, allow_live=False)
        assert err is None

    @pytest.mark.unit
    def test_live_blocked(self):
        mt5 = MagicMock()
        acc = MagicMock()
        acc.trade_mode = 2  # REAL
        acc.login = 12345
        mt5.account_info.return_value = acc

        err = mt5_trade._check_account(mt5, allow_live=False)
        assert err is not None
        assert "[BLOCKED]" in err
        assert "LIVE" in err

    @pytest.mark.unit
    def test_live_allowed(self):
        mt5 = MagicMock()
        acc = MagicMock()
        acc.trade_mode = 2
        acc.login = 12345
        mt5.account_info.return_value = acc

        err = mt5_trade._check_account(mt5, allow_live=True)
        assert err is None


# ============================================================
# Настройки
# ============================================================

class TestConfig:

    @pytest.mark.unit
    def test_set_max_lot(self):
        mt5_trade.set_max_lot(0.5)
        assert mt5_trade.MAX_LOT == 0.5

    @pytest.mark.unit
    def test_set_allow_live(self):
        mt5_trade.set_allow_live(True)
        assert mt5_trade.ALLOW_LIVE is True

    @pytest.mark.unit
    def test_set_confirm_required(self):
        mt5_trade.set_confirm_required(False)
        assert mt5_trade.CONFIRM_REQUIRED is False

    @pytest.mark.unit
    def test_config_status(self):
        status = mt5_trade.get_config_status()
        assert "MAX_LOT" in status
        assert "ALLOW_LIVE" in status
        assert "CONFIRM_REQUIRED" in status


# ============================================================
# Логирование
# ============================================================

class TestLogging:

    @pytest.mark.unit
    def test_log_creates_file(self, tmp_path):
        log_path = tmp_path / "test.log"
        mt5_trade.TRADES_LOG = log_path

        mt5_trade._log_trade("TEST", {"key": "value"})
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "TEST" in content
        assert "value" in content


# ============================================================
# Подтверждение
# ============================================================

class TestConfirmation:

    @pytest.mark.unit
    def test_confirm_callback_set(self):
        def cb(info):
            return True
        mt5_trade.set_confirm_callback(cb)
        assert mt5_trade._confirm_callback is cb

    @pytest.mark.unit
    def test_confirm_callback_reject(self):
        """Callback возвращает False → ордер отменяется."""
        # Мокаем MT5
        with patch.object(mt5_trade, "_mt5") as mock_mt5:
            mt5 = MagicMock()
            acc = MagicMock()
            acc.trade_mode = 0
            acc.login = 12345
            mt5.account_info.return_value = acc

            info = MagicMock()
            info.digits = 2
            info.filling_mode = 2
            info.volume_min = 0.01
            info.volume_max = 100.0
            info.volume_step = 0.01
            mt5.symbol_info.return_value = info

            tick = MagicMock()
            tick.ask = 84000.0
            tick.bid = 84000.0
            mt5.symbol_info_tick.return_value = tick

            mt5.ORDER_TYPE_BUY = 0
            mt5.ORDER_TIME_GTC = 0
            mt5.TRADE_ACTION_DEAL = 1

            mock_mt5.return_value = (mt5, None)

            # Callback отклоняет
            mt5_trade.set_confirm_callback(lambda info: False)
            mt5_trade.CONFIRM_REQUIRED = True

            result = mt5_trade.mt5_order("BTCUSD", "BUY", 0.01)
            assert "[CANCELLED]" in result


# ============================================================
# Неверные аргументы
# ============================================================

class TestValidation:

    @pytest.mark.unit
    def test_invalid_side(self):
        with patch.object(mt5_trade, "_mt5") as mock_mt5:
            mt5 = MagicMock()
            acc = MagicMock()
            acc.trade_mode = 0
            mt5.account_info.return_value = acc

            info = MagicMock()
            info.volume_min = 0.01
            info.volume_max = 100.0
            info.volume_step = 0.01
            info.digits = 2
            info.filling_mode = 2
            mt5.symbol_info.return_value = info

            tick = MagicMock()
            tick.ask = 84000.0
            tick.bid = 84000.0
            mt5.symbol_info_tick.return_value = tick

            mock_mt5.return_value = (mt5, None)
            mt5_trade.CONFIRM_REQUIRED = False

            result = mt5_trade.mt5_order("BTCUSD", "INVALID", 0.01)
            assert "[ERROR]" in result