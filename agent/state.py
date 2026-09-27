"""Сохранение состояния агента между запусками (exhausted-модели)."""

import json
import os
from datetime import date

STATE_FILE = "agent_state.json"


def _today() -> str:
    return date.today().isoformat()


def load_exhausted() -> set:
    """Читает список исчерпанных моделей из файла.
    Если файл старше сегодняшней даты — сбрасывает (квота обновилась)."""
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return set()

    saved_date = data.get("date")
    if saved_date != _today():
        return set()

    exhausted = data.get("exhausted", [])
    if isinstance(exhausted, list):
        return set(exhausted)
    return set()


def save_exhausted(exhausted: set):
    """Сохраняет список исчерпанных моделей с текущей датой."""
    data = {
        "date": _today(),
        "exhausted": sorted(exhausted),
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear_state():
    """Полный сброс состояния."""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    except Exception:
        pass
