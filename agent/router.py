"""Умный выбор модели под задачу.

Теперь все задачи идут в lite — он быстрый (3-5с) и с большой квотой (1500/день).
flash оставлен в каталоге как fallback, но роутер его не выбирает.
"""

import re


def classify(user_text: str) -> str:
    """Классификация пока не используется — всё идёт в lite."""
    return "simple"


def pick_model_key(user_text: str, catalog_keys: list, exhausted: set) -> str | None:
    """
    Выбор модели Gemini.
    Для трейдинга и tool-chains используем flash-3.5 (умнее, но квота 20/день).
    Для остального — lite-3.5 (быстро, квота 1500/день).
    """
    # Проверяем, трейдинг ли это
    import re
    TRADING_KEYWORDS = [
        r"\bбрифинг\b", r"\bанализ\s+(рынка|цены|пары)",
        r"\bчто\s+с\s+(ценой|рынком|парой|золотом|биткоином)",
        r"\bкотировк", r"\bсигнал\s+(на|по)",
        r"\bXAUUSD\b", r"\bBTCUSD\b", r"\bEURUSD\b", r"\bGBPUSD\b",
        r"\bзолото\b", r"\bбиткоин\b",
        r"\bотправь.*телеграм",
    ]
    t = user_text.lower()
    is_trading = any(re.search(p, t) for p in TRADING_KEYWORDS)

    if is_trading:
        # Для трейдинга — flash-3.5 (умеет tool-chains)
        if "flash-3.5" in catalog_keys and "flash-3.5" not in exhausted:
            return "flash-3.5"
        if "lite-3.5" in catalog_keys and "lite-3.5" not in exhausted:
            return "lite-3.5"
    else:
        # Для всего остального — lite-3.5 (экономим квоту)
        if "lite-3.5" in catalog_keys and "lite-3.5" not in exhausted:
            return "lite-3.5"
        if "flash-3.5" in catalog_keys and "flash-3.5" not in exhausted:
            return "flash-3.5"

    return None
