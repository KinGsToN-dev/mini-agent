"""Инструмент http_get — чтение веб-страниц и API."""

import re
import httpx
from urllib.parse import urlparse
from datetime import datetime


ALLOWED_SCHEMES = {"http", "https"}

# Хосты, к которым нельзя обращаться (защита от сканирования локальной сети)
BLOCKED_HOST_PATTERNS = [
    r"^localhost$", r"^127\.", r"^0\.0\.0\.0$",
    r"^10\.", r"^192\.168\.", r"^172\.(1[6-9]|2[0-9]|3[01])\.",
    r"^169\.254\.",   # link-local
    r"^::1$", r"^fe80:",
]

MAX_RESPONSE = 1_048_576   # 1 МБ
CONTEXT_LIMIT = 8000       # сколько символов вернуть модели


def _is_blocked_host(host: str) -> bool:
    h = (host or "").lower()
    for pat in BLOCKED_HOST_PATTERNS:
        if re.search(pat, h):
            return True
    return False


def _decode(raw: bytes, content_type: str) -> str:
    """Пытается декодировать как UTF-8, потом cp1251."""
    # Определяем кодировку из content-type
    m = re.search(r"charset=([\w-]+)", content_type or "", re.IGNORECASE)
    if m:
        enc = m.group(1)
        try:
            return raw.decode(enc, errors="replace")
        except Exception:
            pass
    for enc in ("utf-8", "cp1251", "windows-1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    from agent.log import log
    log("http_get: fallback decode utf-8 with errors=replace", level="DEBUG")
    return raw.decode("utf-8", errors="replace")


def http_get(url: str, timeout: int = 10,
              save_to: str = None) -> str:
    """Делает GET-запрос по URL. Возвращает содержимое."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES:
            return f"[ERROR] Разрешены только http/https, получено: {parsed.scheme}"

        if _is_blocked_host(parsed.hostname):
            return (f"[BLOCKED] Хост {parsed.hostname} заблокирован "
                    f"(localhost / приватные сети запрещены)")

        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "mini-agent/1.0 (Python httpx)"},
        ) as client:
            response = client.get(url)

        content_type = response.headers.get("content-type", "")
        size = len(response.content)

        if size > MAX_RESPONSE:
            return (f"[ERROR] Ответ слишком большой: {size} байт "
                    f"(лимит {MAX_RESPONSE}). Используй save_to= для сохранения.")

        text = _decode(response.content, content_type)

        # Формируем шапку
        header = (
            f"URL: {url}\n"
            f"Статус: {response.status_code} {response.reason_phrase}\n"
            f"Content-Type: {content_type or '?'}\n"
            f"Размер: {size} байт\n"
        )

        # Если save_to — сохраняем в файл
        if save_to:
            try:
                with open(save_to, "w", encoding="utf-8") as f:
                    f.write(text)
                return header + f"\nСохранено в файл: {save_to}"
            except Exception as e:
                return header + f"\n[ERROR] Не удалось сохранить: {e}"

        # Обрезаем если длинно
        if len(text) > CONTEXT_LIMIT:
            text = text[:CONTEXT_LIMIT] + f"\n\n...[обрезано, всего {len(text)} символов]"

        return header + "\n" + text

    except httpx.TimeoutException:
        return f"[ERROR] Таймаут {timeout}с — сайт не отвечает"
    except httpx.ConnectError as e:
        return f"[ERROR] Не удалось подключиться: {e}"
    except httpx.HTTPError as e:
        return f"[ERROR] HTTP-ошибка: {e}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
