"""Общий логгер mini-agent.

Простой интерфейс:
    from agent.log import log
    log("что-то случилось")
    log("что-то сломалось", level="ERROR")
    log("подробности", level="DEBUG")

Уровни: DEBUG, INFO, WARNING, ERROR.
Пишет в agent.log (append, UTF-8).
Не падает, если файл недоступен — просто игнорирует ошибку.
"""

import os
from datetime import datetime


LOG_FILE = "agent.log"

VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

# Минимальный уровень для записи в файл.
# Можно поменять через env: AGENT_LOG_LEVEL=DEBUG
_DEFAULT_LEVEL = os.getenv("AGENT_LOG_LEVEL", "INFO").upper()


def log(msg: str, level: str = "INFO", to_console: bool = False):
    """
    Записать сообщение в agent.log.

    Args:
        msg: текст сообщения.
        level: DEBUG / INFO / WARNING / ERROR.
        to_console: если True — напечатать ещё и в stdout.
    """
    level = (level or "INFO").upper()
    if level not in VALID_LEVELS:
        level = "INFO"

    # Фильтр по уровню
    try:
        min_idx = VALID_LEVELS.index(_DEFAULT_LEVEL)
        cur_idx = VALID_LEVELS.index(level)
        if cur_idx < min_idx:
            return
    except ValueError:
        pass

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


def debug(msg: str, to_console: bool = False):
    log(msg, level="DEBUG", to_console=to_console)


def info(msg: str, to_console: bool = False):
    log(msg, level="INFO", to_console=to_console)


def warning(msg: str, to_console: bool = False):
    log(msg, level="WARNING", to_console=to_console)


def error(msg: str, to_console: bool = False):
    log(msg, level="ERROR", to_console=to_console)
