"""Регистр инструментов и их схем для LLM."""

from .shell import run_shell
from .files import read_file, write_file
from .listdir import list_dir
from .grep import grep
from .processes import processes
from .screenshot import screenshot, screenshot_analyze
from .http_get import http_get
from .clipboard import clipboard
from .notify import notify
from .pyexec import python_exec
from .web_search import web_search
from .mt5_tools import mt5_quote, mt5_bars, mt5_account, mt5_positions, mt5_summary
from .news_tools import econ_calendar
from .telegram_tools import telegram_send


# Глобальный клиент для vision-запросов
_VISION_CLIENT = None


def set_vision_client(client):
    global _VISION_CLIENT
    _VISION_CLIENT = client


TOOL_SCHEMAS = [
    {
        "type": "function", "name": "run_shell",
        "description": "Выполнить команду в терминале Windows (cmd).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Команда, например 'dir'"},
            },
            "required": ["command"],
        },
    },
    {
        "type": "function", "name": "read_file",
        "description": "Прочитать содержимое файла по пути.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Путь к файлу"},
            },
            "required": ["path"],
        },
    },
    {
        "type": "function", "name": "write_file",
        "description": "Записать текст в файл (создать/перезаписать).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "type": "function", "name": "list_dir",
        "description": "Структурированный список файлов и папок в директории.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Путь (по умолчанию '.')"},
                "recursive": {"type": "boolean", "description": "Рекурсивно обходить"},
                "pattern": {"type": "string", "description": "Фильтр по имени, например '*.py'"},
            },
        },
    },
    {
        "type": "function", "name": "grep",
        "description": "Поиск текста (regex) в файлах.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "file_pattern": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["pattern"],
        },
    },
    {
        "type": "function", "name": "processes",
        "description": "Список процессов или kill процесса (action='list'/'kill').",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "kill"]},
                "filter": {"type": "string"},
                "sort_by": {"type": "string", "enum": ["cpu", "memory", "name"]},
                "top": {"type": "integer"},
                "pid": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    {
        "type": "function", "name": "screenshot",
        "description": "Сделать скриншот экрана и сохранить в файл PNG.",
        "parameters": {
            "type": "object",
            "properties": {
                "save_path": {"type": "string"},
            },
        },
    },
    {
        "type": "function", "name": "screenshot_analyze",
        "description": "Скриншот + описание через Gemini vision.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "save_path": {"type": "string"},
            },
        },
    },
    {
        "type": "function", "name": "http_get",
        "description": "GET-запрос по URL (http/https). Локальные адреса запрещены.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout": {"type": "integer"},
                "save_to": {"type": "string"},
            },
            "required": ["url"],
        },
    },
    {
        "type": "function", "name": "clipboard",
        "description": "Работа с буфером обмена: get — прочитать, set — записать.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "set"]},
                "text": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    {
        "type": "function", "name": "notify",
        "description": "Показать Windows-уведомление (toast).",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "message": {"type": "string"},
                "duration": {"type": "integer"},
            },
            "required": ["message"],
        },
    },
    {
        "type": "function", "name": "python_exec",
        "description": "Выполнить Python-код. Запрещены: os, subprocess, eval, exec, open.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "timeout": {"type": "integer"},
                "cwd": {"type": "string"},
            },
            "required": ["code"],
        },
    },
    {
        "type": "function", "name": "web_search",
        "description": "Поиск в интернете через Tavily.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "type": "function", "name": "mt5_quote",
        "description": "Текущая котировка (bid/ask) из MetaTrader 5.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "EURUSD, XAUUSD, GBPUSD..."},
            },
            "required": ["symbol"],
        },
    },
    {
        "type": "function", "name": "mt5_bars",
        "description": "OHLC-свечи из MT5. timeframe: M1, M5, M15, M30, H1, H4, D1, W1, MN1.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["symbol"],
        },
    },
    {
        "type": "function", "name": "mt5_summary",
        "description": "Сводка по символу: цена, изменение 24ч, диапазон, MA(20), MA(50), RSI(14), тренд. Идеально для брифингов.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "EURUSD, XAUUSD, BTCUSD..."},
            },
            "required": ["symbol"],
        },
    },
    {
        "type": "function", "name": "mt5_account",
        "description": "Информация об аккаунте MT5: баланс, equity, маржа.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function", "name": "mt5_positions",
        "description": "Открытые позиции в MT5.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function", "name": "econ_calendar",
        "description": "Экономический календарь. countries: US,EU,GB. importance: low/medium/high/all.",
        "parameters": {
            "type": "object",
            "properties": {
                "countries": {"type": "string"},
                "importance": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "type": "function", "name": "telegram_send",
        "description": "Отправить сообщение в Telegram (chat_id из .env). ВАЖНО: используй ТОЛЬКО имя 'telegram_send'. НЕ пиши текст для копирования — РЕАЛЬНО вызывай этот инструмент. Параметры: message (обязательно), title (опционально, будет жирным). Пример: telegram_send(message='Утренний брифинг BTCUSD: цена $84,880...', title='BTCUSD Briefing').",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["message"],
        },
    },
]


TOOL_FUNCTIONS = {
    "run_shell": run_shell,
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "grep": grep,
    "processes": processes,
    "screenshot": screenshot,
    "screenshot_analyze": screenshot_analyze,
    "http_get": http_get,
    "clipboard": clipboard,
    "notify": notify,
    "python_exec": python_exec,
    "web_search": web_search,
    "mt5_quote": mt5_quote,
    "mt5_summary": mt5_summary,
    "mt5_bars": mt5_bars,
    "mt5_account": mt5_account,
    "mt5_positions": mt5_positions,
    "econ_calendar": econ_calendar,
    "telegram_send": telegram_send,
}


# Алиасы для инструментов — модель иногда путает имена
TOOL_ALIASES = {
    # Telegram
    "send_telegram_message": "telegram_send",
    "send_telegram": "telegram_send",
    "telegram": "telegram_send",
    "send_message": "telegram_send",
    "tg_send": "telegram_send",
    "notify_telegram": "telegram_send",
    # Web
    "search_web": "web_search",
    "google_search": "web_search",
    "search": "web_search",
    # MT5
    "get_quote": "mt5_quote",
    "quote": "mt5_quote",
    "get_bars": "mt5_bars",
    "bars": "mt5_bars",
    "get_account": "mt5_account",
    "account": "mt5_account",
    "get_positions": "mt5_positions",
    "positions": "mt5_positions",
    "summary": "mt5_summary",
    "get_summary": "mt5_summary",
    # News
    "calendar": "econ_calendar",
    "get_calendar": "econ_calendar",
    "economic_calendar": "econ_calendar",
    "news": "econ_calendar",
    # Files
    "read": "read_file",
    "write": "write_file",
    "ls": "list_dir",
    "dir": "list_dir",
    # Shell
    "shell": "run_shell",
    "exec_shell": "run_shell",
    "bash": "run_shell",
    # Python
    "exec_python": "python_exec",
    "py_exec": "python_exec",
    "run_python": "python_exec",
}


def execute_tool(name: str, args: dict) -> str:
    # Проверяем алиасы
    if name in TOOL_ALIASES:
        original = name
        name = TOOL_ALIASES[name]
        # Логируем (полезно для отладки)
        # print(f"[alias] {original} -> {name}")
    
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"[ERROR] Неизвестный инструмент: {name}. Доступные: {list(TOOL_FUNCTIONS.keys())}"
    try:
        return fn(**args)
    except TypeError as e:
        return f"[ERROR] Неверные аргументы для {name}: {e}"