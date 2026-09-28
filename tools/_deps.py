"""
tools/_deps.py — self-healing для внешних зависимостей.

Гарантирует, что MT5 и TradingView запущены, перед использованием.

Проверки:
  - MT5: psutil (быстро, ~30мс) -> fallback на mt5.initialize() (~17с если MT5 закрыт).
  - TradingView: httpx к CDP (~1.5с) -> fallback на start_tradingview.bat (~7с).

Дополнительно:
  - Кэш процесса MT5 (5 секунд).
  - Кэш статуса CDP TradingView (3 секунды).
  - Логирование в deps.log.
  - Оповещение в Telegram при долгом запуске (>5с).
  - MT5_PATH из .env как fallback (для запуска через Popen).
"""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


MT5_PROCESS_NAMES = ("terminal64", "metatrader")
MT5_WAIT_TIMEOUT = 30
TV_CDP_URL = "http://127.0.0.1:9222/json/version"
TV_WAIT_TIMEOUT = 30
TV_START_BAT = "start_tradingview.bat"
TV_START_PS1 = "start_tradingview.ps1"

MT5_CACHE_TTL = 5.0
TV_CACHE_TTL = 3.0

LOG_FILE = "deps.log"

TELEGRAM_NOTIFY_THRESHOLD = 5.0


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _notify_telegram(message: str):
    try:
        from tools.telegram_tools import telegram_send
        telegram_send(message, title="Mini-Agent")
    except Exception as e:
        _log(f"telegram notify failed: {e}")


_mt5_cache = {"time": 0.0, "running": False}


def _mt5_process_running(use_cache: bool = True) -> bool:
    now = time.time()
    if use_cache and (now - _mt5_cache["time"]) < MT5_CACHE_TTL:
        return _mt5_cache["running"]

    try:
        import psutil
    except ImportError:
        _log("psutil not installed, fallback to mt5.initialize")
        return False

    running = False
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if any(p in name for p in MT5_PROCESS_NAMES):
                running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    _mt5_cache["time"] = now
    _mt5_cache["running"] = running
    return running


def _invalidate_mt5_cache():
    _mt5_cache["time"] = 0.0
    _mt5_cache["running"] = False


def _mt5_init_via_module() -> tuple:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return False, "MetaTrader5 not installed"

    if not mt5.initialize():
        err = mt5.last_error()
        mt5.shutdown()
        return False, f"initialize failed: {err}"

    acc = mt5.account_info()
    mt5.shutdown()

    if acc is None:
        return True, "initialized (no account info)"

    mode = "DEMO" if acc.trade_mode == 0 else "LIVE"
    return True, f"account {acc.login} ({mode})"


def _mt5_start_via_popen(exe_path: str) -> bool:
    try:
        subprocess.Popen(
            [exe_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _log(f"Popen: started {exe_path}")
        return True
    except Exception as e:
        _log(f"Popen failed: {type(e).__name__}: {e}")
        return False


def _find_mt5_exe():
    mt5_env = os.getenv("MT5_PATH")
    if mt5_env and Path(mt5_env).is_file():
        return mt5_env

    for p in [
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\FTMO MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    ]:
        if Path(p).is_file():
            return p

    return None


def ensure_mt5_running() -> tuple:
    t0 = time.time()

    if _mt5_process_running(use_cache=True):
        return True, "process running (fast check)"

    _log("MT5 process not found, starting...")
    _notify_telegram("MT5 не запущен, запускаю...")

    ok, msg = _mt5_init_via_module()
    dt = time.time() - t0

    if ok:
        _log(f"MT5 started via initialize() in {dt:.1f}s: {msg}")
        _invalidate_mt5_cache()
        if dt > TELEGRAM_NOTIFY_THRESHOLD:
            _notify_telegram(f"MT5 запущен за {dt:.0f}с")
        return True, msg

    _log(f"initialize() failed in {dt:.1f}s: {msg}")

    exe = _find_mt5_exe()
    if exe and _mt5_start_via_popen(exe):
        deadline = time.time() + MT5_WAIT_TIMEOUT
        while time.time() < deadline:
            time.sleep(1)
            ok2, msg2 = _mt5_init_via_module()
            if ok2:
                dt2 = time.time() - t0
                _log(f"MT5 started via Popen in {dt2:.1f}s: {msg2}")
                _invalidate_mt5_cache()
                _notify_telegram(f"MT5 запущен за {dt2:.0f}с")
                return True, msg2
        return False, f"Popen started but initialize() timeout after {MT5_WAIT_TIMEOUT}s"

    _notify_telegram(f"MT5 не удалось запустить: {msg}")
    return False, msg


_tv_cache = {"time": 0.0, "alive": False}


def _tv_cdp_alive(use_cache: bool = True) -> bool:
    now = time.time()
    if use_cache and (now - _tv_cache["time"]) < TV_CACHE_TTL:
        return _tv_cache["alive"]

    try:
        import httpx
        with httpx.Client(timeout=3) as client:
            r = client.get(TV_CDP_URL)
        alive = r.status_code == 200
    except Exception:
        alive = False

    _tv_cache["time"] = now
    _tv_cache["alive"] = alive
    return alive


def _invalidate_tv_cache():
    _tv_cache["time"] = 0.0
    _tv_cache["alive"] = False


def _tv_chart_tab_ready() -> bool:
    """Проверяет, есть ли вкладка TradingView с chart (не только CDP)."""
    try:
        import httpx
        with httpx.Client(timeout=3) as client:
            r = client.get("http://127.0.0.1:9222/json")
        tabs = r.json()
        for t in tabs:
            if t.get("type") == "page" and "tradingview.com/chart" in t.get("url", ""):
                return True
        return False
    except Exception:
        return False


def ensure_tv_running() -> tuple:
    t0 = time.time()

    if _tv_cdp_alive(use_cache=True):
        return True, "CDP alive (fast check)"

    _log("TradingView CDP not responding, starting...")
    _notify_telegram("TradingView не запущен, запускаю...")

    if Path(TV_START_BAT).is_file():
        cmd = ["cmd", "/c", str(Path(TV_START_BAT).resolve())]
        _log(f"using {TV_START_BAT}")
    elif Path(TV_START_PS1).is_file():
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File",
               str(Path(TV_START_PS1).resolve())]
        _log(f"using {TV_START_PS1}")
    else:
        return False, f"neither {TV_START_BAT} nor {TV_START_PS1} found"

    try:
        subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        _log(f"Popen failed: {type(e).__name__}: {e}")
        return False, f"Popen failed: {e}"

    deadline = time.time() + TV_WAIT_TIMEOUT
    while time.time() < deadline:
        time.sleep(1)
        _invalidate_tv_cache()
        if _tv_cdp_alive(use_cache=False) and _tv_chart_tab_ready():
            dt = time.time() - t0
            _log(f"TradingView CDP + chart tab ready in {dt:.1f}s")
            if dt > TELEGRAM_NOTIFY_THRESHOLD:
                _notify_telegram(f"TradingView запущен за {dt:.0f}с")
            return True, "CDP + chart ready"

    dt = time.time() - t0
    _log(f"TradingView CDP timeout after {dt:.1f}s")
    _notify_telegram(f"TradingView не удалось запустить за {dt:.0f}с")
    return False, f"timeout {TV_WAIT_TIMEOUT}s waiting for CDP"
