"""Инструмент clipboard — работа с буфером обмена (только текст)."""

MAX_CLIP = 100_000   # 100 КБ — защита от зависания


def clipboard(action: str = "get", text: str = None) -> str:
    """get — вернуть содержимое буфера; set — записать."""
    try:
        import pyperclip
    except ImportError:
        return "[ERROR] pyperclip не установлен. Запусти: pip install pyperclip"

    try:
        if action == "get":
            content = pyperclip.paste()
            if not content:
                return "Буфер обмена пуст"
            if len(content) > 5000:
                preview = content[:5000] + f"\n\n...[обрезано, всего {len(content)} символов]"
            else:
                preview = content
            return f"Содержимое буфера ({len(content)} символов):\n{preview}"

        elif action == "set":
            if text is None:
                return "[ERROR] Для action='set' нужен параметр text"
            if len(text) > MAX_CLIP:
                return f"[ERROR] Слишком большой текст: {len(text)} (лимит {MAX_CLIP})"
            pyperclip.copy(text)
            return f"[OK] Скопировано в буфер: {len(text)} символов"

        else:
            return f"[ERROR] action должен быть 'get' или 'set', а не '{action}'"

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
