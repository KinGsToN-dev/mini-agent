"""Безопасность: whitelist инструментов для Telegram."""

from telegram_bot.config import ALLOWED_TOOLS, FORBIDDEN_TOOLS


def is_tool_allowed(tool_name: str) -> bool:
    return tool_name in ALLOWED_TOOLS


def is_tool_forbidden(tool_name: str) -> bool:
    return tool_name in FORBIDDEN_TOOLS


def filter_tools(tools: list) -> list:
    return [t for t in tools if is_tool_allowed(t)]
