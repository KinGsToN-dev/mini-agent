"""Capabilities провайдеров — что каждый умеет.

Зачем это нужно:
- Роутер в agent/core.py должен знать, поддерживает ли провайдер tools.
- Mistral (Codestral) НЕ поддерживает function-calling (у него свой формат API,
  не OpenAI). Если роутер отправит "покажи файлы" в Mistral — он напишет
  `list_dir(path='.')` текстом, а не вызовет tool.
- Gemini/Groq/OpenRouter поддерживают tools через OpenAI-совместимый формат.

Функция pick_provider_for_category учитывает:
1. Категорию запроса (trading, code, general, ...).
2. Намерение в тексте (нужен ли tool для этого запроса).
3. Доступность провайдера (available_providers).
"""

from __future__ import annotations

import re


# ============================================================
# Реестр capabilities
# ============================================================

PROVIDER_CAPABILITIES: dict[str, dict] = {
    "gemini": {
        "supports_tools": True,
        "supports_vision": True,
        "supports_web_search": True,
        "notes": "Универсальный. Vision + tools.",
    },
    "groq": {
        "supports_tools": True,   # но ломает tool-calls при >25 tools
        "supports_vision": False,
        "supports_web_search": False,
        "notes": "Быстрый. Tools только для простых случаев (≤3 итераций).",
    },
    "openrouter": {
        "supports_tools": True,
        "supports_vision": False,
        "supports_web_search": False,
        "notes": "Fallback для Gemini. Llama 3.3 70B хорошо делает tool-calls.",
    },
    "mistral": {
        "supports_tools": False,  # Codestral — свой формат, не OpenAI
        "supports_vision": False,
        "supports_web_search": False,
        "notes": "Для кода без tools. Не использовать для tool-calls.",
    },
}


def provider_supports_tools(provider_name: str) -> bool:
    """Возвращает True, если провайдер поддерживает tools."""
    caps = PROVIDER_CAPABILITIES.get(provider_name, {})
    return bool(caps.get("supports_tools", False))


# ============================================================
# Определение "нужен ли tool"
# ============================================================

# Паттерны — запрос требует вызова инструмента (list_dir, read_file, mt5_summary, ...).
# Если такой паттерн сработал, а провайдер НЕ поддерживает tools — переключаемся.
TOOL_INTENT_PATTERNS = [
    # Файлы
    r"\bпокажи\b", r"\bпосмотри\b", r"\bпрочитай\b", r"\bоткрой\b",
    r"\bсписок\b", r"\bнайди\s+(?:файл|файлы|в\s+проекте|в\s+файлах)",
    r"\bпокажи\s+(?:все\s+)?(?:файл|файлы|\.py|\.md|\.json)",
    r"\bсколько\s+файлов\b",
    r"\bструктур[ау]\s+проекта\b",

    # Трейдинг / данные
    r"\bпроанализируй\b", r"\bанализ\b",
    r"\bсводк[ау]\b", r"\bкотировк[ау]\b",
    r"\bбрифинг\b",
    r"\bсделай\s+брифинг\b",
    r"\bзолот[оаеу]?\b",
    r"\bсеребр[оаеу]?\b",
    r"\bнефт[ьия]\b",
    r"\bбиткоин\b", r"\bбиткойн\b",
    r"\bBTC\b", r"\bETH\b",
    r"\bXAUUSD\b", r"\bXAGUSD\b", r"\bBTCUSD\b", r"\bEURUSD\b",
    r"\bдай\s+анализ\b",
    r"\bпокажи\s+(?:цену|график|свечи)",
    r"\bбаланс\b", r"\bпозици[ияю]\b",
    r"\bкупи\b", r"\bпродай\b", r"\bоткрой\s+позици", r"\bзакрой\s+позици",
    r"\bзакрой\s+вс[её]", r"\bпоставь\s+(?:SL|TP|стоп)",

    # Telegram
    r"\bотправь\b", r"\bскинь\b", r"\bпришли\b", r"\bв\s+телеграм\b",
    r"\bв\s+тг\b",

    # Система
    r"\bпроцесс[ыа]\b", r"\bскриншот\b", r"\bчто\s+на\s+экране\b",
    r"\bбуфер\s+обмена\b", r"\bуведоми\b",

    # Web
    r"\bнайди\s+в\s+интернете\b", r"\bпоищи\b", r"\bпогугли\b",
    r"\bчто\s+нового\b", r"\bпоследние\s+новости\b",

    # TradingView
    r"\btv_analyze\b", r"\btv_screenshot\b",
    r"\bскриншот\s+графика\b", r"\bс\s+графика\b", r"\bс\s+скриншотом\b",
]


def user_needs_tools(user_text: str) -> bool:
    """Эвристика: требует ли запрос вызова tool?

    Если да — провайдер должен поддерживать tools.
    Если нет (просто "напиши функцию") — можно Mistral.
    """
    t = (user_text or "").lower()
    for pattern in TOOL_INTENT_PATTERNS:
        if re.search(pattern, t):
            return True
    return False


# ============================================================
# Главная функция: выбор провайдера с учётом tools
# ============================================================

def pick_provider_for_category(
    category: str,
    user_text: str,
    available: list[str],
) -> str | None:
    """Выбирает провайдера для категории с учётом supports_tools.

    Args:
        category: категория от classifier (trading, code, general, ...).
        user_text: исходный текст запроса.
        available: список доступных провайдеров.

    Returns:
        Имя провайдера или None (если ничего не подходит).
    """
    # Базовый маппинг: категория → предпочитаемый провайдер
    category_to_provider = {
        "trading":    "gemini",
        "vision":     "gemini",
        "code":       "mistral",
        "web_search": "gemini",
        "general":    "groq",
    }
    target = category_to_provider.get(category)
    if target is None:
        return None

    # Если провайдер не доступен — берём fallback
    if target not in available:
        fallback_order = {
            "mistral":    ["gemini", "openrouter", "groq"],
            "gemini":     ["openrouter", "groq"],
            "groq":       ["openrouter", "gemini"],
            "openrouter": ["gemini", "groq"],
        }
        for alt in fallback_order.get(target, []):
            if alt in available:
                target = alt
                break
        else:
            return None

    # ГЛАВНАЯ ЛОГИКА: если запрос требует tools, а провайдер их не умеет —
    # переключаемся на tools-capable провайдера.
    needs_tools = user_needs_tools(user_text)
    if needs_tools and not provider_supports_tools(target):
        # Для code → переключаемся на gemini (лучший для tools + русский)
        if target == "mistral":
            tools_fallback = ["gemini", "openrouter", "groq"]
            for alt in tools_fallback:
                if alt in available:
                    return alt
        # Для остальных — ищем любой tools-capable
        for alt in available:
            if provider_supports_tools(alt):
                return alt
        return None

    return target


# ============================================================
# Утилиты для тестов и отладки
# ============================================================

def describe_capabilities(provider_name: str) -> str:
    """Короткое описание провайдера."""
    caps = PROVIDER_CAPABILITIES.get(provider_name, {})
    if not caps:
        return f"{provider_name}: unknown"
    return (
        f"{provider_name}: "
        f"tools={caps.get('supports_tools')}, "
        f"vision={caps.get('supports_vision')}, "
        f"web_search={caps.get('supports_web_search')}"
    )