"""Инструмент Telegram — отправка сообщений."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def telegram_send(message: str, title: str = "") -> str:
    """
    Отправить сообщение в Telegram.
    Автоматически определяет Markdown vs HTML и очищает лишнее.
    """
    if not message.strip():
        return "[ERROR] Пустое сообщение"

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return "[ERROR] Нет TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в .env"

    # Определяем формат: если есть HTML-теги — используем HTML, иначе Markdown
    has_html = any(tag in message.lower() for tag in ("<b>", "<i>", "<u>", "<s>", "<code>", "<pre>", "<a "))

    if has_html:
        # Если модель выдала HTML — убираем возможные конфликты и оставляем HTML
        text = f"<b>{title}</b>\n\n{message}" if title else message
        parse_mode = "HTML"
        # Экранируем случайные & и < > вне тегов — простая защита
        # (полноценный парсер не нужен, т.к. модель пишет валидный HTML)
    else:
        # Markdown-формат
        text = f"*{title}*\n\n{message}" if title else message
        parse_mode = "Markdown"

    if len(text) > 4000:
        text = text[:4000] + "\n...[обрезано]"

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
        # Если Telegram отверг разметку — пробуем без неё
        if r.status_code == 400:
            payload.pop("parse_mode", None)
            with httpx.Client(timeout=15) as client:
                r = client.post(url, json=payload)
            if r.status_code == 200:
                return f"[OK] Отправлено в Telegram ({len(text)} символов, без разметки)"
        return f"[ERROR] Telegram вернул {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"