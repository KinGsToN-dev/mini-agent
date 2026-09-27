"""Автоматический выбор провайдера под задачу.

Vision → Gemini
Код → Mistral
Всё остальное (включая web search) → Groq (быстрый)
"""

import re

# --- Паттерны -----------------------------------------------------------

# Web search — Groq (у него tool web_search) или Gemini
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

# Аналитика — Gemini flash (умная)
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
    # Web search — Gemini (надёжнее: без проблем с tools и лимитами)
    if _matches(user_text, WEB_SEARCH_PATTERNS):
        if "gemini" in available:
            return "gemini"
        if "groq" in available:
            return "groq"
        return None

    # Vision — только Gemini
    if _matches(user_text, VISION_PATTERNS):
        if "gemini" in available:
            return "gemini"
        # Если Gemini нет — отдадим как есть
        return None

    # Аналитика — Gemini (ДО кода: "проанализируй код" = анализ)
    if _matches(user_text, ANALYSIS_PATTERNS):
        if "gemini" in available:
            return "gemini"
        if "groq" in available:
            return "groq"
        return None

    # Код — Mistral (если есть)
    if _matches(user_text, CODE_PATTERNS):
        if "mistral" in available:
            return "mistral"
        if "groq" in available:
            return "groq"
        return None

    # Всё остальное — Groq (быстрый, щедрая квота)
    if "groq" in available:
        return "groq"

    # Fallback — оставляем как есть
    return None


def describe_decision(user_text: str) -> str:
    """Короткое описание, почему выбран такой провайдер."""
    if _matches(user_text, WEB_SEARCH_PATTERNS):
        return "web_search"
    if _matches(user_text, VISION_PATTERNS):
        return "vision"
    if _matches(user_text, ANALYSIS_PATTERNS):
        return "анализ"
    if _matches(user_text, CODE_PATTERNS):
        return "код"
    return "общее"
