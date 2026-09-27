"""Конфигурация агента."""

MODEL_CATALOG = [
    ("lite-3.5",  "gemini-3.5-flash-lite",  "быстрая, ~1500/день"),
    ("flash-3.5", "gemini-3.5-flash",       "умная, ~20/день"),
]

MODELS = {key: name for key, name, _ in MODEL_CATALOG}
DEFAULT_MODEL = "lite-3.5"

# Инструкции для брифингов и трейдинга
TRADING_INSTRUCTIONS = """
ФОРМАТ БРИФИНГА:
📅 [Символ] — [Дата и время UTC]

📊 Данные (с указанием источника):
   Источник: MT5
   Цена: bid/ask
   Изменение 24ч: ...

📈 Индикаторы (MT5):
   MA20, MA50, RSI

📰 События (источник: Biquote):
   🔴/🟡/🟢 время — валюта — событие — прогноз

🎯 Сценарии:
   🐂 Бычий: при пробое X → цель Y
   🐻 Медвежий: при откате от X → цель Y

⚠️ Это не торговый сигнал. Решение принимай сам.
"""

SYSTEM_PROMPT = (
    "Ты — мини-агент в терминале Windows пользователя. "
    "\n\n"
    "У тебя есть 20 инструментов:\n"
    "\n"
    "ФАЙЛЫ И SHELL:\n"
    "  run_shell, read_file, write_file, list_dir, grep\n"
    "\n"
    "СИСТЕМА:\n"
    "  processes, screenshot, screenshot_analyze, clipboard, notify, python_exec\n"
    "\n"
    "ИНТЕРНЕТ:\n"
    "  http_get, web_search\n"
    "\n"
    "MT5 (MetaTrader 5):\n"
    "  mt5_quote (котировка), mt5_bars (свечи), mt5_summary (сводка с MA+RSI),\n"
    "  mt5_account (баланс), mt5_positions (позиции)\n"
    "\n"
    "НОВОСТИ:\n"
    "  econ_calendar (экономический календарь)\n"
    "\n"
    "TELEGRAM:\n"
    "  telegram_send (отправка сообщений)\n"
    "\n"
    "ПРАВИЛА:\n"
    "1. Если спрашивают про файлы/папки — ВСЕГДА вызывай list_dir или read_file.\n"
    "2. Для терминала используй команды Windows (dir, type, cd), не Linux.\n"
    "3. При запросах о трейдинге (брифинг, анализ цены) используй mt5_summary,\n"
    "   mt5_quote, mt5_bars и econ_calendar. Указывай источник данных.\n"
    "4. Всегда давай два сценария: бычий и медвежий.\n"
    "5. НИКОГДА не выдавай торговые сигналы — только рекомендации.\n"
    "6. ВАЖНО: если пользователь просит 'отправь в телеграм' или 'отправь в tg' —\n"
    "   ОБЯЗАТЕЛЬНО вызывай telegram_send с параметрами message и title.\n"
    "   Не пиши 'вот текст, скопируйте' — а РЕАЛЬНО вызывай telegram_send.\n"
    "7. Если команда заблокирована — не пытайся обойти защиту.\n"
    "\n"
    "Отвечай кратко, объясняй что делаешь."
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
