"""Инструменты скриншотов: screenshot и screenshot_analyze."""

import os
import base64
from datetime import datetime
from pathlib import Path

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _take_screenshot(save_path: str = None) -> Path:
    """Внутренняя функция: делает скриншот, возвращает путь."""
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow не установлен. Запусти: pip install pillow")
    if not save_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"screenshot_{ts}.png"
    img = ImageGrab.grab(all_screens=True)
    path = Path(save_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    return path


def screenshot(save_path: str = None, region: str = "full") -> str:
    """Делает скриншот, сохраняет в PNG. Возвращает путь."""
    try:
        path = _take_screenshot(save_path)
        size_kb = path.stat().st_size / 1024
        return (f"Скриншот сохранён: {path}\n"
                f"Размер файла: {size_kb:.1f} KB\n"
                f"ВАЖНО: содержимое скриншота не передано модели. "
                f"Если нужно описать что на экране — используй screenshot_analyze.")
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


# --- Vision: анализ скриншота через Gemini ---

def _get_agent_client():
    """Возвращает глобальный genai-клиент."""
    from tools.registry import _VISION_CLIENT
    if _VISION_CLIENT is None:
        raise RuntimeError("Vision-клиент не настроен. Перезапусти агента.")
    return _VISION_CLIENT


def screenshot_analyze(prompt: str = "Опиши, что на этом экране.",
                        save_path: str = None) -> str:
    """
    Делает скриншот, отправляет картинку в Gemini и возвращает описание.
    Использует client.models.generate_content (стабильный API с поддержкой изображений).
    """
    try:
        # 1. Скриншот
        path = _take_screenshot(save_path)
        size_kb = path.stat().st_size / 1024

        # 2. Кодируем PNG в base64
        with open(path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("ascii")

        # 3. Отправляем в Gemini через generate_content
        client = _get_agent_client()
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img_b64,
                            }
                        },
                    ],
                }
            ],
        )

        text = response.text if hasattr(response, "text") else str(response)
        return (f"[Скриншот: {path.name}, {size_kb:.1f} KB]\n\n"
                f"Описание от Gemini:\n{text}")
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
