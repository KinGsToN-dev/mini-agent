"""Инструменты TradingView: скриншот графика + анализ через Gemini Vision.

Требует:
- TradingView Desktop с CDP на порту 9222 (см. start_tradingview.ps1).
- GEMINI_API_KEY в .env.

tv_screenshot() — делает PNG-скриншот области графика.
tv_analyze(prompt) — скриншот + Gemini Vision → текстовое описание.
"""

import asyncio

from tools._deps import ensure_tv_running
import base64
import json
import time
from datetime import datetime
from pathlib import Path

import httpx
import websockets

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Конфиг
# ============================================================

CDP_URL = "http://127.0.0.1:9222"
CDP_TIMEOUT = 15
SCREENSHOT_DIR = Path("tv_screenshots")
MIN_SCREENSHOT_SIZE = 5000  # меньше — считаем, что окно свёрнуто

# Модели Gemini с vision (в порядке приоритета)
VISION_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
]


# Последний скриншот и модель, которая его прочитала
_last_screenshot_path = None
_last_vision_model = None


def get_last_screenshot_path() -> str | None:
    """Возвращает путь к последнему скриншоту TradingView."""
    return _last_screenshot_path


def get_last_vision_model() -> str | None:
    """Возвращает имя модели, которая последней читала скриншот."""
    return _last_vision_model


# ============================================================
# CDP — поиск вкладки
# ============================================================

async def _get_tv_tab() -> dict | None:
    """Находит вкладку TradingView через CDP."""
    try:
        async with httpx.AsyncClient(timeout=CDP_TIMEOUT) as client:
            r = await client.get(f"{CDP_URL}/json")
            tabs = r.json()
    except Exception as e:
        raise RuntimeError(
            f"Не могу подключиться к CDP ({CDP_URL}).\n"
            f"Запусти TradingView: start_tradingview.ps1\n"
            f"Ошибка: {e}"
        )

    for t in tabs:
        if t.get("type") == "page" and "tradingview.com/chart" in t.get("url", ""):
            return t
    return None


# ============================================================
# CDP — скриншот
# ============================================================

async def _capture_screenshot(ws_url: str) -> bytes:
    """Делает скриншот через CDP Page.captureScreenshot."""
    async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
        # Page.enable — обязателен
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()

        # Скриншот
        await ws.send(json.dumps({
            "id": 2,
            "method": "Page.captureScreenshot",
            "params": {"format": "png", "fromSurface": True},
        }))
        response = await ws.recv()
        data = json.loads(response)

    result = data.get("result", {})
    if "data" not in result:
        raise RuntimeError(f"CDP не вернул data: {data.get('error', data)}")

    return base64.b64decode(result["data"])


# ============================================================
# Публичная функция: tv_screenshot
# ============================================================

def tv_screenshot(save_path: str = None) -> str:
    """
    Делает скриншот графика TradingView и сохраняет в PNG.

    Args:
        save_path: путь для сохранения (по умолчанию — в tv_screenshots/).

    Returns:
        Путь к сохранённому файлу + размер.
    """
    ok, msg = ensure_tv_running()
    if not ok:
        return f"[ERROR] TradingView unavailable: {msg}"
    try:
        # 1. Найти вкладку
        tv_tab = asyncio.run(_get_tv_tab())
        if tv_tab is None:
            return (
                "[ERROR] Вкладка TradingView не найдена.\n"
                "Открой график в TradingView Desktop.\n"
                "Проверь: http://127.0.0.1:9222/json"
            )

        # 2. Скриншот
        img_bytes = asyncio.run(_capture_screenshot(tv_tab["webSocketDebuggerUrl"]))

        # 3. Проверить размер
        if len(img_bytes) < MIN_SCREENSHOT_SIZE:
            return (
                f"[WARN] Скриншот слишком маленький ({len(img_bytes)} bytes).\n"
                f"Возможно, окно TradingView свёрнуто (minimized).\n"
                f"Разверни окно (не minimize) и попробуй снова."
            )

        # 4. Сохранить
        if save_path is None:
            SCREENSHOT_DIR.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = SCREENSHOT_DIR / f"tv_{ts}.png"
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

        save_path.write_bytes(img_bytes)
        global _last_screenshot_path
        _last_screenshot_path = str(save_path)
        return f"[OK] Скриншот сохранён: {save_path} ({len(img_bytes)} bytes)"

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


# ============================================================
# Публичная функция: tv_analyze (Gemini Vision)
# ============================================================

def tv_analyze(prompt: str = None) -> str:
    ok, msg = ensure_tv_running()
    if not ok:
        return f"[ERROR] TradingView unavailable: {msg}"
    # FIX: save context BEFORE asyncio.run, because ContextVar is lost inside
    _saved_chat_id = None
    _saved_use_cmd = False
    try:
        from tools.registry import get_tool_context
        _ctx = get_tool_context() or {}
        _saved_chat_id = _ctx.get("chat_id")
        _saved_use_cmd = bool(_ctx.get("use_command_bot"))
    except Exception as e:
        from agent.log import log
        log(f"tradingview: get_tool_context failed: {type(e).__name__}: {e}", level="DEBUG")
    """
    Делает скриншот TradingView и отправляет в Gemini Vision.

    Args:
        prompt: что спросить у Gemini. По умолчанию — просьба прочитать
                все индикаторы графика.

    Returns:
        Текстовое описание от Gemini.
    """
    if not prompt:
        prompt = (
            "Это график TradingView. Прочитай ВСЕ видимые данные:\n"
            "1. Bias-дашборд (по таймфреймам 15m, 1H, 4H, 1D) — Bear/Bull/WAIT.\n"
            "2. Score-таблица — значения типа 2/0.\n"
            "3. BXO — WEAK BUY / WEAK SELL / STRONG BUY / STRONG SELL.\n"
            "4. Структура рынка на графике: BOS, CHoCH, IDM, FVG, Order Blocks.\n"
            "5. Уровни ликвидности (Buy-side / Sell-side).\n"
            "6. Зоны Premium / Equilibrium / Discount.\n"
            "7. MACD, RSI, OBV, MFI — числовые значения.\n"
            "8. Тикер и текущая цена.\n"
            "Отвечай КРАТКО, списком. Только факты с графика."
        )

    # 1. Скриншот
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    img_path = SCREENSHOT_DIR / f"tv_analyze_{ts}.png"

    # FIX: ретрай — CDP может быть готов, а вкладка с chart ещё грузится
    screenshot_result = tv_screenshot(str(img_path))
    if not screenshot_result.startswith("[OK]"):
        import time as _time
        _time.sleep(3)
        screenshot_result = tv_screenshot(str(img_path))
    if not screenshot_result.startswith("[OK]"):
        return f"[ERROR] Не удалось сделать скриншот:\n{screenshot_result}"

    # 2. Base64
    try:
        img_b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
    except Exception as e:
        return f"[ERROR] Не могу прочитать скриншот: {e}"

    # 3. Gemini Vision
    try:
        import os
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "[ERROR] Нет GEMINI_API_KEY в .env"

        client = genai.Client(api_key=api_key)

        last_error = None
        for model in VISION_MODELS:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(
                            data=base64.b64decode(img_b64),
                            mime_type="image/png",
                        ),
                        prompt,
                    ],
                )
                text = response.text if hasattr(response, "text") else str(response)
                if text:
                    global _last_vision_model
                    _last_vision_model = model
                    # NOTE: photo is sent by the agent (Gemini) via telegram_send_photo
                    # (see SYSTEM_PROMPT: "ПОСЛЕ tv_analyze — отправь скриншот").
                    # Do NOT send here — иначе дубликат скриншота.
                    return f"[Модель: {model}]\n[Скриншот: {img_path}]\n\n{text}"
            except Exception as e:
                last_error = e
                continue

        return f"[ERROR] Все vision-модели недоступны. Последняя ошибка: {last_error}"

    except Exception as e:
        return f"[ERROR] Gemini: {type(e).__name__}: {e}"
