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

def _tg_log(msg: str):
    from datetime import datetime
    try:
        with open('telegram_debug.log', 'a', encoding='utf-8') as f:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f'[{ts}] {msg}' + chr(10))
    except Exception:
        pass

# FIX: get_tool_context импортируется лениво (внутри функций),
# чтобы избежать circular import с tools/registry.py.
def _get_ctx() -> dict:
    """Лениво достаёт tool context. Возвращает {} при ошибке."""
    try:
        from tools.registry import get_tool_context
        return get_tool_context() or {}
    except ImportError:
        return {}


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
    try:
        from tools.registry import get_tool_context
        _ctx = get_tool_context()
    except Exception:
        _ctx = None

    if not message.strip():
        return "[ERROR] Пустое сообщение"

    # FIX: force command bot if available in env
    import os as _os
    if not use_command_bot and _os.getenv("TELEGRAM_COMMAND_BOT_TOKEN"):
        use_command_bot = True

    # --- Читаем контекст (если он есть) ---
    ctx = _get_ctx()
    ctx_chat_id = ctx.get("chat_id")
    ctx_use_command_bot = bool(ctx.get("use_command_bot"))

    # --- Приоритет: параметр > контекст > env ---
    effective_chat_id = chat_id if chat_id is not None else ctx_chat_id
    effective_use_command_bot = use_command_bot or ctx_use_command_bot
    _tg_log(f"TG_SEND: param={chat_id}, ctx={ctx_chat_id}, eff={effective_chat_id}, use_cmd={effective_use_command_bot}")

    # --- Токен ---
    if effective_use_command_bot:
        token = os.getenv("TELEGRAM_COMMAND_BOT_TOKEN")
        token_name = "TELEGRAM_COMMAND_BOT_TOKEN"
    else:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        token_name = "TELEGRAM_BOT_TOKEN"

    if not token:
        return f"[ERROR] Нет {token_name} в .env"

    # --- chat_id ---
    if effective_chat_id is None:
        chat_id_raw = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_raw:
            return "[ERROR] Нет TELEGRAM_CHAT_ID в .env и не передан chat_id"
        try:
            effective_chat_id = int(chat_id_raw)
        except ValueError:
            return f"[ERROR] Некорректный TELEGRAM_CHAT_ID: {chat_id_raw!r}"

    chat_id = effective_chat_id

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

def telegram_send_photo(
    photo_path: str,
    caption: str = "",
    chat_id: int = None,
    use_command_bot: bool = False,
) -> str:
    """
    Отправить фото (PNG/JPEG) в Telegram через sendPhoto.

    Логика выбора токена и chat_id — как в telegram_send.
    """
    import os
    from pathlib import Path

    # --- Проверка файла ---
    # FIX: force command bot if available in env
    import os as _os2
    if not use_command_bot and _os2.getenv("TELEGRAM_COMMAND_BOT_TOKEN"):
        use_command_bot = True

    p = Path(photo_path)
    if not p.exists():
        return f"[ERROR] Файл не найден: {photo_path}"
    if not p.is_file():
        return f"[ERROR] Это не файл: {photo_path}"

    size_kb = p.stat().st_size / 1024
    if size_kb > 10000:  # 10 MB — лимит Telegram
        return f"[ERROR] Файл слишком большой: {size_kb:.0f} KB (лимит 10 MB)"

    # --- Контекст (chat_id, use_command_bot) ---
    ctx = _get_ctx()
    ctx_chat_id = ctx.get("chat_id")
    ctx_use_command_bot = bool(ctx.get("use_command_bot"))

    effective_chat_id = chat_id if chat_id is not None else ctx_chat_id
    effective_use_command_bot = use_command_bot or ctx_use_command_bot
    _tg_log(f"TG_PHOTO: param={chat_id}, ctx={ctx_chat_id}, eff={effective_chat_id}, use_cmd={effective_use_command_bot}, photo={photo_path}")

    # --- Токен ---
    if effective_use_command_bot:
        token = os.getenv("TELEGRAM_COMMAND_BOT_TOKEN")
        token_name = "TELEGRAM_COMMAND_BOT_TOKEN"
    else:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        token_name = "TELEGRAM_BOT_TOKEN"

    if not token:
        return f"[ERROR] Нет {token_name} в .env"

    # --- chat_id ---
    if effective_chat_id is None:
        chat_id_raw = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_raw:
            return "[ERROR] Нет TELEGRAM_CHAT_ID в .env и не передан chat_id"
        try:
            effective_chat_id = int(chat_id_raw)
        except ValueError:
            return f"[ERROR] Некорректный TELEGRAM_CHAT_ID: {chat_id_raw!r}"

    if len(caption) > 1000:
        caption = caption[:1000] + "..."

    # --- Отправка ---
    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        with httpx.Client(timeout=30) as client:
            with open(p, "rb") as photo_file:
                files = {"photo": (p.name, photo_file, "image/png")}
                data = {"chat_id": str(effective_chat_id)}
                if caption:
                    data["caption"] = caption
                    data["parse_mode"] = "Markdown"

                r = client.post(url, data=data, files=files)

        if r.status_code == 200:
            return f"[OK] Фото отправлено в Telegram ({size_kb:.0f} KB)"
        return f"[ERROR] Telegram вернул {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"

