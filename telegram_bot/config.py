"""Конфигурация Telegram-бота."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_token() -> str:
    token = os.getenv("TELEGRAM_COMMAND_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_COMMAND_BOT_TOKEN не найден в .env.")
    return token


def get_allowed_chat_ids() -> set:
    raw = os.getenv("TELEGRAM_COMMAND_ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        raise RuntimeError("TELEGRAM_COMMAND_ALLOWED_CHAT_IDS не найден в .env.")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            raise RuntimeError(f"Некорректный chat_id: {part!r}")
    return ids


def get_agent_server_url() -> str:
    return os.getenv("AGENT_SERVER_URL", "http://127.0.0.1:8765")


TELEGRAM_API_BASE = "https://api.telegram.org"
POLL_TIMEOUT = 30
TELEGRAM_MAX_LENGTH = 4096
SPLIT_LENGTH = 4000

ALLOWED_TOOLS = {
    "read_file", "list_dir", "grep",
    "mt5_quote", "mt5_bars", "mt5_summary", "mt5_account", "mt5_positions",
    "mt5_order", "mt5_close", "mt5_close_all", "mt5_modify", "mt5_pending",
    "econ_calendar", "web_search", "http_get",
    "screenshot", "screenshot_analyze",
    "telegram_send",
}

FORBIDDEN_TOOLS = {
    "run_shell", "write_file", "python_exec", "clipboard", "notify", "processes",
}
