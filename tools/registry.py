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

# Глобальный клиент для vision-запросов.
# Устанавливается из agent/core.py при инициализации.
_VISION_CLIENT = None


def set_vision_client(client):
    """Регистрирует genai-клиент для vision-функций."""
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
        "description": ("Структурированный список файлов и папок в директории. "
                       "Лучше чем run_shell('dir'). Поддерживает рекурсию и фильтр по имени."),
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
        "description": ("Поиск текста (regex) в файлах. Используй для поиска "
                       "определений, использования, TODO, ошибок."),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Регулярное выражение"},
                "path": {"type": "string", "description": "Где искать (по умолчанию '.')"},
                "file_pattern": {"type": "string", "description": "Фильтр по файлам, например '*.py'"},
                "max_results": {"type": "integer", "description": "Максимум результатов (по умолчанию 50)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "type": "function", "name": "processes",
        "description": ("Список процессов (action='list') или убийство процесса (action='kill'). "
                       "Используй для диагностики 'что грузит CPU' или закрытия зависших приложений."),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "kill"]},
                "filter": {"type": "string", "description": "Фильтр по имени процесса"},
                "sort_by": {"type": "string", "enum": ["cpu", "memory", "name"]},
                "top": {"type": "integer", "description": "Сколько показать (по умолчанию 15)"},
                "pid": {"type": "integer", "description": "PID для kill"},
                "name": {"type": "string", "description": "Имя процесса для kill"},
            },
            "required": ["action"],
        },
    },
    {
        "type": "function", "name": "screenshot",
        "description": "Сделать скриншот экрана и сохранить в файл PNG (без анализа).",
        "parameters": {
            "type": "object",
            "properties": {
                "save_path": {"type": "string", "description": "Куда сохранить"},
            },
        },
    },
    {
        "type": "function", "name": "screenshot_analyze",
        "description": ("Сделать скриншот экрана И ОПИСАТЬ его содержимое через Gemini vision. "
                       "Используй, когда пользователь спрашивает 'что на экране', "
                       "'прочитай ошибку', 'опиши окно' и т.п."),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string",
                          "description": "Что именно спросить про скриншот (по умолчанию 'Опиши что на экране')"},
                "save_path": {"type": "string", "description": "Куда сохранить PNG"},
            },
        },
    },
    {
        "type": "function", "name": "http_get",
        "description": ("Сделать GET-запрос по URL и получить содержимое "
                       "(HTML, JSON, текст). Используй для чтения веб-страниц, "
                       "документации, API. Только http/https. Локальные адреса запрещены."),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Полный URL с http:// или https://"},
                "timeout": {"type": "integer", "description": "Секунды (по умолчанию 10)"},
                "save_to": {"type": "string", "description": "Сохранить в файл вместо возврата"},
            },
            "required": ["url"],
        },
    },
    {
        "type": "function", "name": "clipboard",
        "description": ("Работа с буфером обмена: get — прочитать, set — записать. "
                       "Только текст."),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "set"]},
                "text": {"type": "string", "description": "Что записать (для action='set')"},
            },
            "required": ["action"],
        },
    },
    {
        "type": "function", "name": "notify",
        "description": ("Показать Windows-уведомление (toast). Используй для "
                       "оповещения о завершении длинных задач."),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Заголовок"},
                "message": {"type": "string", "description": "Текст уведомления"},
                "duration": {"type": "integer", "description": "Секунды (по умолчанию 5)"},
            },
            "required": ["message"],
        },
    },
    {
        "type": "function", "name": "python_exec",
        "description": ("Выполнить Python-код и вернуть stdout/stderr. "
                       "Используй для вычислений, парсинга JSON, обработки текста. "
                       "Запрещены: os, subprocess, shutil, eval, exec, open."),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python-код"},
                "timeout": {"type": "integer", "description": "Секунды (по умолчанию 30)"},
                "cwd": {"type": "string", "description": "Рабочая директория"},
            },
            "required": ["code"],
        },
    },
    {
        "type": "function", "name": "web_search",
        "description": ("Поиск в интернете через DuckDuckGo. Возвращает список "
                       "результатов: заголовок + URL + описание. Используй, когда "
                       "нужна актуальная информация из интернета."),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос"},
                "max_results": {"type": "integer", "description": "Максимум результатов (по умолчанию 8)"},
            },
            "required": ["query"],
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
}


def execute_tool(name: str, args: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"[ERROR] Неизвестный инструмент: {name}"
    try:
        return fn(**args)
    except TypeError as e:
        return f"[ERROR] Неверные аргументы для {name}: {e}"


