"""Инструмент Telegram — отправка сообщений.

Поддерживает два режима:
1. Legacy — использует TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID.
2. Командный — использует TELEGRAM_COMMAND_BOT_TOKEN и chat_id,
   откуда пришла команда.
"""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


def telegram_send(
    message: str,
    title: str = "",
    chat_id: Optional[int] = None,
    use_command_bot: bool = False,
) -> str:
    """
    Отправить сообщение в Telegram.

    Args:
        message: текст сообщения.
        title: заголовок (будет жирным).
        chat_id: если задан — отправить в этот чат. Если None — использовать
                 TELEGRAM_CHAT_ID из .env.
        use_command_bot: если True — использовать токен
                         TELEGRAM_COMMAND_BOT_TOKEN. Если False — TELEGRAM_BOT_TOKEN.
    """
    if not message.strip():
        return "[ERROR] Пустое сообщение"

    # --- Токен ---
    if use_command_bot:
        token = os.getenv("TELEGRAM_COMMAND_BOT_TOKEN")
        token_name = "TELEGRAM_COMMAND_BOT_TOKEN"
    else:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        token_name = "TELEGRAM_BOT_TOKEN"

    if not token:
        return f"[ERROR] Нет {token_name} в .env"

    # --- chat_id ---
    if chat_id is None:
        chat_id_raw = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_raw:
            return "[ERROR] Нет TELEGRAM_CHAT_ID в .env и не передан chat_id"
        try:
            chat_id = int(chat_id_raw)
        except ValueError:
            return f"[ERROR] Некорректный TELEGRAM_CHAT_ID: {chat_id_raw!r}"

    # --- Определяем формат ---
    has_html = any(
        tag in message.lower()
        for tag in ("<b>", "<i>", "<u>", "<s>", "<code>", "<pre>", "<a ")
    )

    if has_html:
        text = f"<b>{title}</b>\n\n{message}" if title else message
        parse_mode = "HTML"
    else:
        text = f"*{title}*\n\n{message}" if title else message
        parse_mode = "Markdown"

    if len(text) > 4000:
        text = text[:4000] + "\n...[обрезано]"

    # --- Отправка ---
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        with httpx.Client(timeout=15) as client:
            r = client.post(url, json=payload)
        if r.status_code == 200:
            return f"[OK] Отправлено в Telegram ({len(text)} символов, {parse_mode})"

        if r.status_code == 400:
            # Возможно, проблема с разметкой — пробуем без неё
            payload.pop("parse_mode", None)
            with httpx.Client(timeout=15) as client:
                r = client.post(url, json=payload)
            if r.status_code == 200:
                return f"[OK] Отправлено в Telegram ({len(text)} символов, без разметки)"

        return f"[ERROR] Telegram вернул {r.status_code}: {r.text[:200]}"

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
