"""Обработка сообщений Telegram → HTTP-запросы к agent_server."""

import logging
from typing import Optional

import httpx

from telegram_bot import config


logger = logging.getLogger(__name__)


HELP_TEXT = """*Mini-Agent Telegram Bot*

Просто напиши команду агенту:
- дай анализ по золоту
- покажи мои позиции
- найди в интернете новости про BTC

*Команды:*
/start   - приветствие
/help    - эта справка
/status  - статус сервера
/reset   - сбросить историю

Опасные команды (shell, запись файлов) не выполняются через Telegram.
"""

START_TEXT = """Привет! Я - Telegram-бот mini-agent.

Пиши команды агенту - он выполнит и ответит. /help - справка.
"""


def session_id_for_chat(chat_id: int) -> str:
    return f"tg_{chat_id}"


def _post(url: str, payload: dict, timeout: float = 300.0) -> dict:
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload)
    except httpx.ConnectError:
        raise RuntimeError(
            f"Сервер недоступен: {url}\n"
            f"Запусти: python scripts/run_agent_server.py"
        )
    except httpx.TimeoutException:
        raise RuntimeError(f"Таймаут {timeout}с - сервер не отвечает")
    except httpx.HTTPError as e:
        raise RuntimeError(f"HTTP-ошибка: {e}")

    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"Сервер вернул {r.status_code}: {detail}")

    return r.json()


def _get(url: str, timeout: float = 10.0) -> dict:
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
    except httpx.ConnectError:
        raise RuntimeError(f"Сервер недоступен: {url}")
    except httpx.HTTPError as e:
        raise RuntimeError(f"HTTP-ошибка: {e}")
    if r.status_code >= 400:
        raise RuntimeError(f"Сервер вернул {r.status_code}")
    return r.json()


def handle_message(chat_id: int, text: str, username: Optional[str] = None) -> str:
    base = config.get_agent_server_url()
    sid = session_id_for_chat(chat_id)
    text = (text or "").strip()

    if not text:
        return "Пустое сообщение."

    if text.startswith("/start"):
        return START_TEXT

    if text.startswith("/help"):
        return HELP_TEXT

    if text.startswith("/status"):
        try:
            data = _get(f"{base}/status")
            return (
                f"*Статус сервера*\n"
                f"Провайдер: {data.get('provider')}\n"
                f"Модель: {data.get('model')}\n"
                f"Режим: {data.get('mode')}"
            )
        except RuntimeError as e:
            return str(e)

    if text.startswith("/reset"):
        try:
            _post(f"{base}/reset", {"session_id": sid})
            return "История диалога сброшена."
        except RuntimeError as e:
            return str(e)

    logger.info("chat=%s user=%s msg=%r", chat_id, username, text[:80])

    try:
        data = _post(f"{base}/ask", {"text": text, "session_id": sid, "chat_id": chat_id})
    except RuntimeError as e:
        return str(e)

    answer = data.get("answer", "(пустой ответ)")
    provider = data.get("provider", "?")
    model = data.get("model", "?")
    dt = data.get("duration_ms", 0)

    footer = f"\n\n_({provider} / {model}, {dt} мс)_"
    return answer + footer


def split_message(text: str, limit: int = None) -> list:
    if limit is None:
        limit = config.SPLIT_LENGTH
    if len(text) <= limit:
        return [text]

    parts = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        parts.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()
    if remaining:
        parts.append(remaining)
    return parts
