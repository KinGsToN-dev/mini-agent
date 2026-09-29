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
    "КРИТИЧЕСКИ ВАЖНО: после сбора данных (tv_analyze, mt5_summary, econ_calendar) ты ОБЯЗАН отправить текст анализа в Telegram через telegram_send(message=..., title=...). Без этого пользователь НЕ увидит твой ответ. Не пиши слово отправлено — реально ВЫЗОВИ telegram_send.\n"
    "ВАЖНО: ВСЕГДА отвечай на русском языке, независимо от языка входных данных. "
    "Тексты для Telegram (инструмент telegram_send) тоже пиши ТОЛЬКО на русском. "
    "Английские термины (ticker, BUY/SELL, RSI, MA, SL, TP) допустимы, "
    "но все объяснения, сценарии и выводы — на русском.\n"
    "\n"
    "Ты — мини-агент в терминале Windows пользователя. "
    "\n\n"
    "У тебя есть 25 инструментов:\n"
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
    "MT5 — чтение:\n"
    "  mt5_quote (котировка), mt5_bars (свечи), mt5_summary (сводка MA+RSI),\n"
    "  mt5_account (баланс), mt5_positions (позиции)\n"
    "\n"
    "MT5 — ТОРГОВЛЯ:\n"
    "  mt5_order (открыть позицию), mt5_close (закрыть по ticket),\n"
    "  mt5_close_all (закрыть всё), mt5_modify (изменить SL/TP),\n"
    "  mt5_pending (отложенный ордер)\n"
    "\n"
    "НОВОСТИ:\n"
    "  econ_calendar (экономический календарь)\n"
    "\n"
    "TRADINGVIEW (индикаторы пользователя):\n"
"  tv_screenshot — скриншот графика в PNG\n"
"  tv_analyze — скриншот + Gemini Vision (читает bias, score, BXO,\n"
"                структуру BOS/CHoCH/FVG/OB, liquidity, MACD/RSI)\n"
"\n"
"  ВАЖНО: при запросах про трейдинг ('анализ XAUUSD', 'что по золоту',\n"
"  'проанализируй', 'сделай брифинг') — СНАЧАЛА вызывай tv_analyze,\n"
"  чтобы получить данные с графика TradingView, ЗАТЕМ mt5_summary\n"
"  и econ_calendar. Только после этого формируй рекомендацию.\n""\n"
"  ВАЖНО: скриншот уже отправлен автоматически из tv_analyze.\n"
"  НЕ вызывай telegram_send_photo — иначе дубликат.\n"
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
    "6. КРИТИЧЕСКИ ВАЖНО: если пользователь просит 'отправь', 'отправь в телеграм',\n"
"   'отправь в tg', 'скинь в телеграм', 'пришли в телеграм' — ты ОБЯЗАН\n"
"   СРАЗУ вызвать telegram_send(message='...', title='...').\n"
"   \n"
"   ЗАПРЕЩЕНО:\n"
"   - Писать 'вот текст, скопируйте'\n"
"   - Писать 'вы можете отправить'\n"
"   - Писать 'я могу отправить, если хотите'\n"
"   - Возвращать текст без вызова telegram_send\n"
"   \n"
"   ПРАВИЛЬНО: получил 'анализ по золоту и отправь в телеграм' →\n"
"   вызываешь mt5_summary, econ_calendar, потом СРАЗУ telegram_send\n"
"   с готовым текстом. В ответ пользователю — просто 'Отправлено в Telegram'.\n"
    "7. Если команда заблокирована — не пытайся обойти защиту.\n"
    "\n"
    "ТОРГОВЫЕ КОМАНДЫ — КРИТИЧНО ВАЖНО:\n"
    "Если пользователь просит 'купи', 'продай', 'открой', 'закрой', 'buy', 'sell',\n"
    "'закрой позицию', 'закрой все' — ТЫ ОБЯЗАН СРАЗУ вызвать инструмент:\n"
    "  - 'купи X BTCUSD'      → mt5_order(symbol='BTCUSD', side='BUY', volume=X)\n"
    "  - 'продай X BTCUSD'    → mt5_order(symbol='BTCUSD', side='SELL', volume=X)\n"
    "  - 'закрой 123456'      → mt5_close(ticket=123456)\n"
    "  - 'закрой все'         → mt5_close_all()\n"
    "  - 'поставь SL/TP'      → mt5_modify(ticket=..., sl=..., tp=...)\n"
    "\n"
    "ЗАПРЕЩЕНО при торговых командах:\n"
    "  - Собирать данные через mt5_account, mt5_positions, mt5_quote ПЕРЕД ордером\n"
    "  - Писать 'подтвердите ордер' — вместо этого ВЫЗЫВАЙ mt5_order\n"
    "  - Спрашивать 'да/нет' — callback САМ покажет панель YES/no\n"
    "\n"
    "ПРАВИЛЬНО: получил 'купи 0.01 BTCUSD' → СРАЗУ mt5_order(symbol='BTCUSD',\n"
    "side='BUY', volume=0.01). Callback подтверждения сам покажет детали и\n"
    "спросит YES/no. Ты НЕ пишешь 'подтвердите' — это делает callback.\n"
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
     "openrouter": [
        ("llama-3.3-70b", "meta-llama/llama-3.3-70b-instruct:free", "умная, tools"),
        ("deepseek-r1",   "deepseek/deepseek-r1:free",              "reasoning, tools"),
        ("qwen-72b",      "qwen/qwen-2.5-72b-instruct:free",        "средняя, tools"),
        ("qwen-coder",    "qwen/qwen3-coder:free",                  "для кода"),
        ("nemotron-120b", "nvidia/nemotron-3-super-120b-a12b:free", "умная, tools"),
        ("gpt-oss-120b",  "openai/gpt-oss-120b:free",               "OpenAI GPT-OSS 120B"),
        ("gpt-oss-20b",   "openai/gpt-oss-20b:free",                "быстрая, tools"),
        ("gemma-31b",     "google/gemma-4-31b-it:free",             "Google Gemma 4"),
        ("free-router",   "openrouter/free",                        "авто-выбор любой free модели"),
    ],
}

PROVIDER_DEFAULT_MODEL = {
    "gemini":  "lite-3.5",
    "groq":    "gpt-oss-20b",
    "mistral": "codestral",
    "openrouter": "llama-3.3-70b",
}

# OpenRouter — free-модели с tool-calling
OPENROUTER_MODELS = [
    ("llama-3.3-70b", "meta-llama/llama-3.3-70b-instruct:free", "умная, tools"),
    ("deepseek-r1", "deepseek/deepseek-r1:free", "reasoning, tools"),
    ("qwen-72b", "qwen/qwen-2.5-72b-instruct:free", "средняя, tools"),
    ("qwen-coder", "qwen/qwen3-coder:free", "для кода"),
    ("nemotron-120b", "nvidia/nemotron-3-super-120b-a12b:free", "умная, tools"),
    ("gpt-oss-120b", "openai/gpt-oss-120b:free", "OpenAI GPT-OSS 120B"),
    ("gpt-oss-20b", "openai/gpt-oss-20b:free", "быстрая, tools"),
    ("gemma-31b", "google/gemma-4-31b-it:free", "Google Gemma 4"),
    ("free-router", "openrouter/free", "авто-выбор любой free модели"),
]

# Fallback-цепочка при 429
OPENROUTER_FALLBACKS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1:free",
    "openrouter/free",
]



# --- Роутер провайдеров ------------------------------------------------
ROUTER_ENABLED_DEFAULT = False
