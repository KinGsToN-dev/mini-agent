"""Локальное хранение сообщений диалога в JSONL.

Формат: sessions/<имя>.jsonl, одна строка = одна JSON-запись.
Записи: {"ts": "...", "role": "user|agent", "text": "..."}
"""

import json
import os
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = "sessions"


def _ensure_dir():
    Path(SESSIONS_DIR).mkdir(parents=True, exist_ok=True)


def _messages_path(session_name: str) -> str:
    """Путь к JSONL-файлу сессии."""
    safe = "".join(c for c in session_name if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError("Имя сессии должно содержать буквы или цифры")
    return os.path.join(SESSIONS_DIR, f"{safe}.jsonl")


def append_message(session_name: str, role: str, text: str):
    """Добавляет сообщение в JSONL. Одна строка — один JSON-объект."""
    if not session_name:
        return
    _ensure_dir()
    path = _messages_path(session_name)
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "role": role,       # "user" | "agent"
        "text": text,
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_messages(session_name: str) -> list:
    """Загружает все сообщения сессии. Возвращает список dict."""
    if not session_name:
        return []
    path = _messages_path(session_name)
    if not os.path.exists(path):
        return []
    messages = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return messages


def count_messages(session_name: str) -> int:
    return len(load_messages(session_name))


def clear_messages(session_name: str):
    """Удаляет JSONL-файл сессии."""
    path = _messages_path(session_name)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def find_in_messages(query: str, session_names: list = None) -> list:
    """
    Ищет query во всех сообщениях сохранённых сессий.
    Возвращает список dict: {"session": ..., "ts": ..., "role": ..., "text": ...}
    """
    if session_names is None:
        session_names = _list_session_names()

    q = query.lower()
    hits = []
    for name in session_names:
        for msg in load_messages(name):
            if q in (msg.get("text") or "").lower():
                hits.append({
                    "session": name,
                    "ts": msg.get("ts"),
                    "role": msg.get("role"),
                    "text": msg.get("text", "")[:200],
                })
    return hits


def _list_session_names() -> list:
    """Список имён сессий (по JSONL-файлам)."""
    if not os.path.isdir(SESSIONS_DIR):
        return []
    names = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.endswith(".jsonl") and not fname.startswith("_"):
            names.append(fname[:-6])  # убираем ".jsonl"
    return names
