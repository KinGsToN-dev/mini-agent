"""Тесты для tools/_deps.py — self-healing MT5 и TradingView."""
from unittest.mock import MagicMock, patch
import time

import pytest

from tools import _deps


@pytest.fixture(autouse=True)
def reset_caches():
    _deps._invalidate_mt5_cache()
    _deps._invalidate_tv_cache()
    yield
    _deps._invalidate_mt5_cache()
    _deps._invalidate_tv_cache()


class TestMT5ProcessRunning:

    @pytest.mark.unit
    def test_process_found(self):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "terminal64.exe"}
        with patch("psutil.process_iter", return_value=[mock_proc]):
            assert _deps._mt5_process_running(use_cache=False) is True

    @pytest.mark.unit
    def test_process_not_found(self):
        with patch("psutil.process_iter", return_value=[]):
            assert _deps._mt5_process_running(use_cache=False) is False

    @pytest.mark.unit
    def test_process_found_metatrader(self):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "MetaTrader5.exe"}
        with patch("psutil.process_iter", return_value=[mock_proc]):
            assert _deps._mt5_process_running(use_cache=False) is True

    @pytest.mark.unit
    def test_cache_hit(self):
        mock_proc = MagicMock()
        mock_proc.info = {"name": "terminal64.exe"}
        with patch("psutil.process_iter", return_value=[mock_proc]) as mock_iter:
            _deps._mt5_process_running(use_cache=False)
            _deps._mt5_process_running(use_cache=True)
            assert mock_iter.call_count == 1


class TestEnsureMT5:

    @pytest.mark.unit
    def test_fast_path_process_running(self):
        with patch.object(_deps, "_mt5_process_running", return_value=True), \
             patch.object(_deps, "_mt5_init_via_module") as mock_init:
            ok, msg = _deps.ensure_mt5_running()
            assert ok is True
            assert "fast" in msg
            mock_init.assert_not_called()

    @pytest.mark.unit
    def test_slow_path_initialize_ok(self):
        with patch.object(_deps, "_mt5_process_running", return_value=False), \
             patch.object(_deps, "_mt5_init_via_module",
                          return_value=(True, "account 12345 (DEMO)")), \
             patch.object(_deps, "_notify_telegram"):
            ok, msg = _deps.ensure_mt5_running()
            assert ok is True
            assert "account 12345" in msg

    @pytest.mark.unit
    def test_slow_path_initialize_fail_popen_fail(self):
        with patch.object(_deps, "_mt5_process_running", return_value=False), \
             patch.object(_deps, "_mt5_init_via_module",
                          return_value=(False, "initialize failed")), \
             patch.object(_deps, "_find_mt5_exe", return_value=None), \
             patch.object(_deps, "_notify_telegram"):
            ok, msg = _deps.ensure_mt5_running()
            assert ok is False
            assert "initialize failed" in msg

    @pytest.mark.unit
    def test_initialized_without_account(self):
        with patch.object(_deps, "_mt5_process_running", return_value=False), \
             patch.object(_deps, "_mt5_init_via_module",
                          return_value=(True, "initialized (no account info)")), \
             patch.object(_deps, "_notify_telegram"):
            ok, msg = _deps.ensure_mt5_running()
            assert ok is True


class TestTVCDP:

    @pytest.mark.unit
    def test_cdp_alive(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
            assert _deps._tv_cdp_alive(use_cache=False) is True

    @pytest.mark.unit
    def test_cdp_not_responding(self):
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = \
                Exception("connection refused")
            assert _deps._tv_cdp_alive(use_cache=False) is False

    @pytest.mark.unit
    def test_cdp_cache_hit(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
            _deps._tv_cdp_alive(use_cache=False)
            _deps._tv_cdp_alive(use_cache=True)
            assert mock_client.call_count == 1


class TestEnsureTV:

    @pytest.mark.unit
    def test_fast_path_cdp_alive(self):
        with patch.object(_deps, "_tv_cdp_alive", return_value=True), \
             patch("subprocess.Popen") as mock_popen:
            ok, msg = _deps.ensure_tv_running()
            assert ok is True
            assert "fast" in msg
            mock_popen.assert_not_called()

    @pytest.mark.unit
    def test_no_start_script(self):
        with patch.object(_deps, "_tv_cdp_alive", return_value=False), \
             patch.object(_deps, "_notify_telegram"), \
             patch("pathlib.Path.is_file", return_value=False):
            ok, msg = _deps.ensure_tv_running()
            assert ok is False
            # Сообщение: "neither start_tradingview.bat nor start_tradingview.ps1 found"
            assert "neither" in msg or "found" in msg

    @pytest.mark.unit
    def test_popen_fail(self):
        with patch.object(_deps, "_tv_cdp_alive", return_value=False), \
             patch.object(_deps, "_notify_telegram"), \
             patch("pathlib.Path.is_file", return_value=True), \
             patch("subprocess.Popen", side_effect=PermissionError("denied")):
            ok, msg = _deps.ensure_tv_running()
            assert ok is False
            assert "denied" in msg or "failed" in msg.lower()


class TestFindMT5Exe:

    @pytest.mark.unit
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("MT5_PATH", r"C:\custom\terminal64.exe")
        with patch("pathlib.Path.is_file", return_value=True):
            assert _deps._find_mt5_exe() == r"C:\custom\terminal64.exe"

    @pytest.mark.unit
    def test_standard_path(self, monkeypatch):
        monkeypatch.delenv("MT5_PATH", raising=False)
        with patch("pathlib.Path.is_file", side_effect=[False, True]):
            result = _deps._find_mt5_exe()
            assert result is not None

    @pytest.mark.unit
    def test_not_found(self, monkeypatch):
        monkeypatch.delenv("MT5_PATH", raising=False)
        with patch("pathlib.Path.is_file", return_value=False):
            assert _deps._find_mt5_exe() is None


class TestLogging:

    @pytest.mark.unit
    def test_log_writes(self, tmp_path, monkeypatch):
        log_file = tmp_path / "deps.log"
        monkeypatch.setattr(_deps, "LOG_FILE", str(log_file))
        _deps._log("test message")
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "test message" in content

class TestTVChartTabReady:

    @pytest.mark.unit
    def test_chart_tab_found(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"type": "page", "url": "https://www.tradingview.com/chart/abc/"},
            {"type": "page", "url": "about:blank"},
        ]
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
            assert _deps._tv_chart_tab_ready() is True

    @pytest.mark.unit
    def test_chart_tab_not_found(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"type": "page", "url": "about:blank"},
        ]
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
            assert _deps._tv_chart_tab_ready() is False

    @pytest.mark.unit
    def test_chart_tab_connection_error(self):
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = \
                Exception("connection refused")
            assert _deps._tv_chart_tab_ready() is False
