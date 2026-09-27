"""Инструмент Telegram — отправка сообщений."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def telegram_send(message: str, title: str = "") -> str:
    """
    Отправить сообщение в Telegram.
    Требует TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env.
    """
    if not message.strip():
        return "[ERROR] Пустое сообщение"

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return "[ERROR] Нет TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в .env"

    text = f"*{title}*\n\n{message}" if title else message
    if len(text) > 4000:
        text = text[:4000] + "\n...[обрезано]"

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        with httpx.Client(timeout=15) as client:
            r = client.post(url, json=payload)
        if r.status_code == 200:
            return f"[OK] Отправлено в Telegram ({len(text)} символов)"
        return f"[ERROR] Telegram вернул {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"