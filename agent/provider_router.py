"""Автоматический выбор провайдера под задачу.

Торговые действия (купи/продай/открой/закрой) → Gemini flash
Трейдинг (брифинг, анализ цены) → Gemini
Vision → Gemini
Web search → Gemini
Анализ → Gemini
Код → Mistral
Общее → Groq
"""

import re

# --- Паттерны -----------------------------------------------------------

# Торговые действия — открытие/закрытие/модификация
TRADE_ACTION_PATTERNS = [
    r"\b(купи|продай|открой|закрой|открыть|закрыть)\b",
    r"\b(buy|sell|open|close)\s+\d",
    r"\bBUY\b", r"\bSELL\b",
    r"\b(lot|лота|лотов|объём|объем)\s+\d",
    r"\d+\.\d+\s+(BTCUSD|XAUUSD|EURUSD|GBPUSD|USDJPY|AUDUSD)",
    r"\b(BTCUSD|XAUUSD|EURUSD|GBPUSD)\s+(BUY|SELL)",
    r"\b(SL|TP|стоп|тейк)\s+\d",
    r"\bпозици",
    r"\bордер\b",
    r"\bзакрыть\s+вс[её]",
]

# Web search — Gemini (у него tool web_search и лучше результаты)
WEB_SEARCH_PATTERNS = [
    r"\bнайди\b.*\b(в интернете|в сети|в гугл|онлайн)\b",
    r"\bпоищи\b",
    r"\bпогугли\b",
    r"\bзагугли\b",
    r"\bпоиск\b.*\b(в интернете|онлайн)\b",
    r"\bчто нового\b",
    r"\bпоследние новости\b",
    r"\bсвежая информация\b",
    r"\bактуальн\w+\b",
    r"\bsearch\b.*\b(web|internet|online)\b",
    r"\bgoogle\b.*\bfor\b",
    r"\bfind online\b",
]

# Трейдинг — Gemini (брифинг, анализ цены, котировки)
TRADING_PATTERNS = [
    r"\bбрифинг\b",
    r"\bанализ\s+(рынка|цены|пары|символа)",
    r"\bанализ\b.*\b(золот|золото|xauusd|биткоин|btcusd|eurusd|gbpusd|нефт|серебр)",
    r"\b(золот|золото|xauusd|биткоин|btcusd|eurusd|gbpusd)",
    r"\bчто\s+с\s+(ценой|рынком|парой)",
    r"\bпосмотри\s+(цену|котировк|график)",
    r"\bпроанализируй\s+(цену|рынок|символ|XAU|BTC|EUR|GBP|USD)",
    r"\bкотировк",
    r"\bсигнал\s+(на|по)",
    r"\b(покупка|продажа|лонг|шорт)\b",
    r"\bXAUUSD\b", r"\bBTCUSD\b", r"\bEURUSD\b", r"\bGBPUSD\b",
    r"\bзолото\b", r"\bбиткоин\b", r"\bбиткойн\b",
    r"\bчто\s+с\s+\w+",
    r"\bкак\s+дела\s+с\b",
]

# Vision — нужен Gemini (он один умеет картинки)
VISION_PATTERNS = [
    r"\bэкран\b", r"\bскриншот", r"\bскрин\b",
    r"\bпосмотри\b", r"\bпокажи\b.*\b(что|как)\b",
    r"\bчто (на|у меня на) экране\b",
    r"\bпрочитай.*\b(экран|ошибк)",
    r"\bопиши.*(окно|экран|скрин)",
    r"\bscreenshot\b",
    r"\bscreen\b",
    r"\bwindow\b",
    r"\bvision\b",
]

# Аналитика — Gemini
ANALYSIS_PATTERNS = [
    r"\bпроанализируй\b",
    r"\bобъясни почему\b",
    r"\bдокажи\b",
    r"\bсравни\b",
    r"\bисследуй\b",
    r"\bподробно\b.*\bобъясни\b",
    r"\banalyze\b",
    r"\bexplain why\b",
    r"\bcompare\b",
    r"\bdesign\b",
    r"\bархитектур",
    r"\bспроектируй\b",
]

# Код — Mistral Codestral (заточен под код)
CODE_PATTERNS = [
    r"\bнапиши\b.*\b(функци|класс|скрипт|код|программ)",
    r"\bсоздай\b.*\b(функци|класс|скрипт|модул)",
    r"\bреализуй\b",
    r"\bкод\b",
    r"\bфункци",
    r"\bскрипт\b",
    r"\bкласс\b",
    r"\bмодул",
    r"\bалгоритм\b",
    r"\bпарсер\b",
    r"\brefactor\b",
    r"\bdebug\b",
    r"\bотлад",
    r"\bcode\b",
    r"\bfunction\b",
    r"\bscript\b",
    r"\bclass\b",
    r"\bнапиши.*(quicksort|сортировк)",
    r"\b(напиши|создай|реализуй).*\b(python|javascript|java|c\+\+)\b",
]


def _matches(text: str, patterns: list) -> bool:
    t = text.lower()
    for p in patterns:
        if re.search(p, t):
            return True
    return False


def pick_provider(user_text: str, available: list,
                  current_provider: str = "gemini") -> str | None:
    """
    Возвращает имя провайдера для запроса или None (если не решил).
    available — список доступных провайдеров из registry.
    """
    # Торговые действия — ПЕРВЫМИ (Groq быстрый и умеет tools)
    if _matches(user_text, TRADE_ACTION_PATTERNS):
        for p in ("groq", "gemini", "openrouter"):
            if p in available:
                return p
        return None

    # Трейдинг — Gemini (брифинг, анализ цены)
    if _matches(user_text, TRADING_PATTERNS):
        for p in ("groq", "gemini", "openrouter"):
            if p in available:
                return p
        return None

    # Web search — Gemini/OpenRouter/Groq
    if _matches(user_text, WEB_SEARCH_PATTERNS):
        for p in ("gemini", "openrouter", "groq"):
            if p in available:
                return p
        return None

    # Vision — только Gemini
    if _matches(user_text, VISION_PATTERNS):
        if "gemini" in available:
            return "gemini"
        return None

    # Аналитика — Gemini/OpenRouter/Groq
    if _matches(user_text, ANALYSIS_PATTERNS):
        for p in ("gemini", "openrouter", "groq"):
            if p in available:
                return p
        return None

    # Код — Mistral/OpenRouter/Groq
    if _matches(user_text, CODE_PATTERNS):
        for p in ("mistral", "openrouter", "groq"):
            if p in available:
                return p
        return None

    # Всё остальное — Groq/OpenRouter
    for p in ("groq", "openrouter"):
        if p in available:
            return p

    return None


def describe_decision(user_text: str) -> str:
    """Короткое описание, почему выбран такой провайдер."""
    if _matches(user_text, TRADE_ACTION_PATTERNS):
        return "торговое действие"
    if _matches(user_text, TRADING_PATTERNS):
        return "трейдинг"
    if _matches(user_text, WEB_SEARCH_PATTERNS):
        return "web_search"
    if _matches(user_text, VISION_PATTERNS):
        return "vision"
    if _matches(user_text, ANALYSIS_PATTERNS):
        return "анализ"
    if _matches(user_text, CODE_PATTERNS):
        return "код"
    return "общее"