"""Экспорт диалога сессии в Markdown (полный, с сообщениями)."""

import json
import os
from datetime import datetime

from agent import history as history_mod

SESSIONS_DIR = "sessions"


def export_session(session_name: str, out_path: str) -> str:
    """
    Экспортирует сессию в Markdown-файл — с полным диалогом.
    """
    safe = "".join(c for c in session_name if c.isalnum() or c in "-_")
    meta_path = os.path.join(SESSIONS_DIR, f"{safe}.json")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Сессия не найдена: {session_name}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    messages = history_mod.load_messages(session_name)

    lines = [
        f"# Сессия: {meta.get('name', session_name)}",
        "",
        f"**Модель:** {meta.get('model', '?')}",
        f"**Создана:** {meta.get('created', '?')}",
        f"**Обновлена:** {meta.get('updated', '?')}",
        f"**Сообщений:** {len(messages)}",
        "",
        "---",
        "",
    ]

    if not messages:
        lines.append("_(сообщения не сохранены — сессия была до обновления)_")
    else:
        for msg in messages:
            role = msg.get("role", "?")
            ts = msg.get("ts", "")
            text = msg.get("text", "")
            if role == "user":
                lines.append(f"### 👤 you [{ts}]")
            else:
                lines.append(f"### 🤖 agent [{ts}]")
            lines.append("")
            lines.append(text)
            lines.append("")
            lines.append("---")
            lines.append("")

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    return out_path
