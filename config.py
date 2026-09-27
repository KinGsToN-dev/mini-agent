"""Конфигурация агента."""

MODEL_CATALOG = [
    ("lite-3.5",  "gemini-3.5-flash-lite",  "быстрая, ~1500/день"),
    ("flash-3.5", "gemini-3.5-flash",       "умная, ~20/день"),
]

MODELS = {key: name for key, name, _ in MODEL_CATALOG}
DEFAULT_MODEL = "lite-3.5"

SYSTEM_PROMPT = (
    "Ты — мини-агент в терминале Windows пользователя. "
    "У тебя есть инструменты: run_shell, read_file, write_file, list_dir, grep, "
    "processes, screenshot, screenshot_analyze, http_get, clipboard, notify, python_exec. "
    "ВАЖНО: если пользователь спрашивает про файлы, папки, содержимое директории — "
    "ВСЕГДА вызывай list_dir или read_file, а не угадывай содержимое. "
    "Для терминала используй команды Windows (dir, type, cd и т.д.), не Linux. "
    "Отвечай кратко, объясняй что делаешь. "
    "Если команда была заблокирована или отклонена пользователем — не пытайся "
    "обойти защиту, просто сообщи об этом."
)

MAX_TOOL_ITERATIONS = 10
LOG_FILE = "agent.log"

PROVIDER_CATALOG = {
    "gemini": [
        ("lite-3.5",  "gemini-3.5-flash-lite",  "быстрая, ~1500/день"),
        ("flash-3.5", "gemini-3.5-flash",       "умная, ~20/день"),
    ],
    "groq": [
        ("gpt-oss-120b", "openai/gpt-oss-120b",  "умная, GPT-OSS 120B"),
        ("gpt-oss-20b",  "openai/gpt-oss-20b",   "быстрая, GPT-OSS 20B"),
        ("qwen-27b",     "qwen/qwen3.8-27b",     "средняя, Qwen 3.8 27B"),
        ("allam",        "allam-2-7b",           "очень быстрая, 7B"),
    ],
    "mistral": [
        ("codestral", "codestral-latest",      "для кода, 2000/день"),
        ("large",     "mistral-large-latest",  "требует data-training"),
        ("small",     "mistral-small-latest",  "требует data-training"),
        ("nemo",      "open-mistral-nemo",     "может не работать"),
    ],
}

PROVIDER_DEFAULT_MODEL = {
    "gemini":  "lite-3.5",
    "groq":    "gpt-oss-20b",       # qwen не имеет встроенных tools
    "mistral": "codestral",
}

# --- Роутер провайдеров ------------------------------------------------
ROUTER_ENABLED_DEFAULT = True
