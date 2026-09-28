"""Общий логгер mini-agent.

Интерфейс:
    from agent.log import log
    log("что-то случилось")
    log("что-то сломалось", level="ERROR")
    log("подробности", level="TRACE")

Уровни (по возрастанию):
    TRACE    — очень детально, для отладки
    DEBUG    — отладочная информация
    INFO     — обычные события
    WARNING  — не критично, но стоит внимания
    ERROR    — операция не удалась, но агент продолжает
    CRITICAL — серьёзная проблема, надо вмешаться
    FATAL    — всё сломалось, дальше работать нельзя

Пишет в agent.log (append, UTF-8).
Не падает, если файл недоступен — просто игнорирует ошибку.
Уровень фильтрации: env AGENT_LOG_LEVEL (по умолчанию INFO).
"""

import os
from datetime import datetime


LOG_FILE = "agent.log"

# От низкого к высокому
LEVELS = ("TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL")

# Синонимы
LEVEL_ALIASES = {
    "WARN": "WARNING",
    "CRIT": "CRITICAL",
}

# Минимальный уровень для записи (всё, что ниже — игнорируется)
_DEFAULT_LEVEL = (os.getenv("AGENT_LOG_LEVEL", "INFO") or "INFO").upper()


def _normalize_level(level: str) -> str:
    level = (level or "INFO").upper()
    level = LEVEL_ALIASES.get(level, level)
    if level not in LEVELS:
        return "INFO"
    return level


def _should_log(level: str) -> bool:
    try:
        return LEVELS.index(level) >= LEVELS.index(_DEFAULT_LEVEL)
    except ValueError:
        return True


def log(msg: str, level: str = "INFO", to_console: bool = False):
    """
    Записать сообщение в agent.log.

    Args:
        msg: текст сообщения.
        level: TRACE / DEBUG / INFO / WARNING / ERROR / CRITICAL / FATAL.
        to_console: если True — напечатать ещё и в stdout.
    """
    level = _normalize_level(level)
    if not _should_log(level):
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"

    if to_console:
        try:
            print(line)
        except Exception:
            pass

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def trace(msg: str, to_console: bool = False):
    log(msg, level="TRACE", to_console=to_console)


def debug(msg: str, to_console: bool = False):
    log(msg, level="DEBUG", to_console=to_console)


def info(msg: str, to_console: bool = False):
    log(msg, level="INFO", to_console=to_console)


def warning(msg: str, to_console: bool = False):
    log(msg, level="WARNING", to_console=to_console)


def warn(msg: str, to_console: bool = False):
    warning(msg, to_console=to_console)


def error(msg: str, to_console: bool = False):
    log(msg, level="ERROR", to_console=to_console)


def critical(msg: str, to_console: bool = False):
    log(msg, level="CRITICAL", to_console=to_console)


def fatal(msg: str, to_console: bool = False):
    log(msg, level="FATAL", to_console=to_console)
