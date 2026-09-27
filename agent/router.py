"""Умный выбор модели под задачу.

Теперь все задачи идут в lite — он быстрый (3-5с) и с большой квотой (1500/день).
flash оставлен в каталоге как fallback, но роутер его не выбирает.
"""

import re


def classify(user_text: str) -> str:
    """Классификация пока не используется — всё идёт в lite."""
    return "simple"


def pick_model_key(user_text: str, catalog_keys: list, exhausted: set) -> str | None:
    """Всегда возвращает lite, если он не исчерпан."""
    if "lite-3.5" in catalog_keys and "lite-3.5" not in exhausted:
        return "lite-3.5"
    # Fallback: если lite исчерпан — flash
    if "flash-3.5" in catalog_keys and "flash-3.5" not in exhausted:
        return "flash-3.5"
    return None
