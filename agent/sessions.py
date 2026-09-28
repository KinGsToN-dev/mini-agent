"""Сохранение и загрузка сессий диалога."""

import json
import os
from datetime import datetime
from pathlib import Path

from agent import history as history_mod

SESSIONS_DIR = "sessions"
LAST_SESSION_FILE = "sessions/_last.json"


def _ensure_dir():
    Path(SESSIONS_DIR).mkdir(parents=True, exist_ok=True)


def _session_path(name: str) -> str:
    # Защита от путей вида "../evil"
    safe = "".join(c for c in name if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError("Имя сессии должно содержать буквы или цифры")
    return os.path.join(SESSIONS_DIR, f"{safe}.json")


def list_sessions() -> list:
    """Возвращает список сохранённых сессий с метаданными."""
    _ensure_dir()
    sessions = []
    for fname in os.listdir(SESSIONS_DIR):
        if not fname.endswith(".json") or fname.startswith("_"):
            continue
        path = os.path.join(SESSIONS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "name": data.get("name", fname[:-5]),
                "created": data.get("created", "?"),
                "updated": data.get("updated", "?"),
                "model": data.get("model", "?"),
                "message_count": data.get("message_count", 0),
                "preview": data.get("preview", ""),
            })
        except Exception as e:
            from agent.log import log
            log(f"sessions: bad file '{fname}': {type(e).__name__}: {e}", level="DEBUG")
            continue
    # Сортируем по дате обновления (свежие сверху)
    sessions.sort(key=lambda s: s.get("updated", ""), reverse=True)
    return sessions


def save_session(name: str, agent) -> str:
    """Сохраняет текущую сессию агента под именем name."""
    _ensure_dir()
    path = _session_path(name)

    # Считаем реальное количество сообщений из JSONL
    message_count = history_mod.count_messages(name)

    # created берём из старого файла, если он есть
    created = datetime.now().isoformat(timespec="seconds")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                old = json.load(f)
            created = old.get("created", created)
        except Exception:
            pass

    # Агент теперь знает своё имя сессии — для записи в JSONL
    agent.current_session_name = name

    data = {
        "name": name,
        "created": created,
        "updated": datetime.now().isoformat(timespec="seconds"),
        "model": agent.model_name,
        "model_key": agent.model_key,
        "last_interaction_id": agent.last_interaction_id,
        "message_count": message_count,
        "preview": _get_preview(agent),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    _set_last(name)
    return path


def load_session(name: str, agent) -> dict:
    """Загружает сессию в агента. Возвращает метаданные."""
    path = _session_path(name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Сессия не найдена: {name}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    agent.last_interaction_id = data.get("last_interaction_id")
    # Восстанавливаем модель
    from config import MODELS
    mk = data.get("model_key")
    if mk and mk in MODELS:
        agent.model_key = mk
        agent.model_name = MODELS[mk]

    # Устанавливаем имя сессии для дальнейших записей в JSONL
    agent.current_session_name = name

    _set_last(name)
    return data


def _set_last(name: str):
    """Запоминает имя последней активной сессии для автосохранения."""
    _ensure_dir()
    try:
        with open(LAST_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"name": name}, f)
    except Exception as e:
        from agent.log import log
        log(f"sessions: _set_last('{name}') failed: {type(e).__name__}: {e}", level="WARNING")


def get_last_name() -> str | None:
    """Имя последней активной сессии (для автосохранения при выходе)."""
    if not os.path.exists(LAST_SESSION_FILE):
        return None
    try:
        with open(LAST_SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("name")
    except Exception as e:
        from agent.log import log
        log(f"sessions: get_last_name failed: {type(e).__name__}: {e}", level="WARNING")
        return None


def _get_preview(agent) -> str:
    """Превью последнего сообщения. Если пусто — читаем из старого файла."""
    msg = getattr(agent, "last_user_message", "") or ""
    if msg.strip():
        return msg[:80]
    name = get_last_name()
    if name:
        try:
            path = _session_path(name)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    old = json.load(f)
                return old.get("preview", "")
        except Exception as e:
            from agent.log import log
            log(f"sessions: _get_preview failed: {type(e).__name__}: {e}", level="DEBUG")
    return ""


def delete_session(name: str) -> str:
    """Удаляет сессию: и .json, и .jsonl. Возвращает имя удалённой."""
    safe = "".join(c for c in name if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError("Имя сессии должно содержать буквы или цифры")

    json_path = os.path.join(SESSIONS_DIR, f"{safe}.json")
    jsonl_path = os.path.join(SESSIONS_DIR, f"{safe}.jsonl")

    deleted_any = False
    if os.path.exists(json_path):
        os.remove(json_path)
        deleted_any = True
    if os.path.exists(jsonl_path):
        os.remove(jsonl_path)
        deleted_any = True

    if not deleted_any:
        raise FileNotFoundError(f"Сессия не найдена: {name}")

    # Если удалили последнюю активную — сбросить метку
    if get_last_name() == safe:
        try:
            os.remove(LAST_SESSION_FILE)
        except Exception as e:
            from agent.log import log
            log(f"sessions: delete last '{safe}' failed: {type(e).__name__}: {e}", level="DEBUG")

    return name


def rename_session(old_name: str, new_name: str) -> str:
    """Переименовывает сессию (json + jsonl)."""
    old_safe = "".join(c for c in old_name if c.isalnum() or c in "-_")
    new_safe = "".join(c for c in new_name if c.isalnum() or c in "-_")

    if not old_safe or not new_safe:
        raise ValueError("Имена должны содержать буквы или цифры")

    old_json = os.path.join(SESSIONS_DIR, f"{old_safe}.json")
    new_json = os.path.join(SESSIONS_DIR, f"{new_safe}.json")

    if not os.path.exists(old_json):
        raise FileNotFoundError(f"Сессия не найдена: {old_name}")
    if os.path.exists(new_json):
        raise FileExistsError(f"Сессия с именем '{new_name}' уже существует")

    # Переименовываем .json
    os.rename(old_json, new_json)

    # Обновляем name внутри файла
    try:
        with open(new_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["name"] = new_safe
        data["updated"] = datetime.now().isoformat(timespec="seconds")
        with open(new_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        from agent.log import log
        log(f"sessions: rename '{old_name}' json update failed: {type(e).__name__}: {e}", level="WARNING")

    # Переименовываем .jsonl (если есть)
    old_jsonl = os.path.join(SESSIONS_DIR, f"{old_safe}.jsonl")
    new_jsonl = os.path.join(SESSIONS_DIR, f"{new_safe}.jsonl")
    if os.path.exists(old_jsonl):
        os.rename(old_jsonl, new_jsonl)

    # Если это была последняя активная — обновить метку
    if get_last_name() == old_safe:
        _set_last(new_safe)

    return new_safe


def autosave(agent):
    """Автосохранение текущей сессии, если была активна."""
    name = get_last_name()
    if not name:
        return
    try:
        save_session(name, agent)
    except Exception as e:
        from agent.log import log
        log(f"sessions: autosave('{name}') failed: {type(e).__name__}: {e}", level="WARNING")



