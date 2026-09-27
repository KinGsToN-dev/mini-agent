"""Умный классификатор запросов: гибрид regex + LLM.

Логика:
1. Сначала пробуем regex (provider_router.pick_provider) — быстро и бесплатно.
2. Если regex уверенно определил категорию — возвращаем сразу.
3. Если не уверен — спрашиваем Groq allam-2-7b (короткий промпт, один вызов).
4. Если LLM упал или ответил ерунду — возвращаемся к regex.

Возвращает (category, confidence, source):
    category   — 'trading' | 'vision' | 'code' | 'web_search' | 'general'
    confidence — 0.0 .. 1.0
    source     — 'regex' | 'llm' | 'fallback'
"""

from functools import lru_cache

from agent import provider_router


# Категории, которые понимает классификатор
VALID_CATEGORIES = {"trading", "vision", "code", "web_search", "general"}

# Провайдер и модель для классификации (Groq allam-2-7b — быстрая и бесплатная)
CLASSIFIER_PROVIDER = "groq"
CLASSIFIER_MODEL = "allam-2-7b"

# Промпт для LLM — очень короткий, чтобы ответ был быстрым
CLASSIFIER_PROMPT = """\
Отнеси запрос пользователя к ОДНОЙ категории.
Категории: trading, vision, code, web_search, general.
Ответь ОДНИМ словом — только название категории, без объяснений.

trading — трейдинг, котировки, анализ рынка, ордера, позиции, золото/биткоин/валюты, брифинги
vision — что на экране, скриншот, прочитай ошибку на экране
code — напиши функцию, рефакторинг, объясни код, скрипт
web_search — найди в интернете, поищи новости, погугли
general — всё остальное

Запрос: "{text}"
Ответ:"""


@lru_cache(maxsize=200)
def _classify_llm(text: str) -> str | None:
    """Спрашивает LLM. Возвращает категорию или None при ошибке."""
    try:
        from providers import registry as provider_registry

        provider = provider_registry.get_provider(CLASSIFIER_PROVIDER)
        if provider is None:
            return None

        messages = [
            {"role": "system", "content": "Ты — классификатор запросов. Отвечай одним словом."},
            {"role": "user", "content": CLASSIFIER_PROMPT.format(text=text)},
        ]

        answer = provider.ask(
            model_name=CLASSIFIER_MODEL,
            messages=messages,
            tools=None,
        )

        if not answer:
            return None

        # Берём первое слово из ответа, очищаем
        word = answer.strip().lower().split()[0] if answer.strip() else ""
        word = word.strip(".,!?:;\"'`*#-")

        if word in VALID_CATEGORIES:
            return word
        return None
    except Exception:
        return None


def _regex_category(user_text: str, available: list) -> str | None:
    """Пробуем regex-роутер. Возвращает категорию или None."""
    provider = provider_router.pick_provider(user_text, available)
    if provider is None:
        return None

    # Провайдер → категория
    if provider == "mistral":
        return "code"
    if provider == "gemini":
        # vision или web_search или trading — зависит от запроса
        reason = provider_router.describe_decision(user_text)
        if reason == "vision":
            return "vision"
        if reason == "web_search":
            return "web_search"
        if reason == "трейдинг":
            return "trading"
        return "general"
    if provider == "groq":
        # Groq — дефолтный, но regex мог выбрать его для trading (наш приоритет)
        reason = provider_router.describe_decision(user_text)
        if reason == "трейдинг" or reason == "торговое действие":
            return "trading"
        return "general"
    if provider == "openrouter":
        return "general"
    return None


def classify(user_text: str, available: list = None) -> tuple:
    """
    Классифицирует запрос.
    Возвращает (category, confidence, source).
    """
    if not user_text or not user_text.strip():
        return ("general", 0.5, "regex")

    if available is None:
        try:
            from providers import registry as provider_registry
            available = provider_registry.available_providers()
        except Exception:
            available = ["gemini", "groq", "mistral", "openrouter"]

    # 1. Regex
    regex_cat = _regex_category(user_text, available)

    # 2. Если regex уверенно определил категорию И это не "general" — возвращаем.
    #    "general" от regex означает "не уверен" → идём в LLM.
    if regex_cat and regex_cat != "general":
        return (regex_cat, 0.8, "regex")

    # 3. LLM
    llm_cat = _classify_llm(user_text)
    if llm_cat:
        return (llm_cat, 0.9, "llm")

    # 4. Fallback — regex сказал general или ничего не сказал
    if regex_cat:
        return (regex_cat, 0.5, "fallback")
    return ("general", 0.4, "fallback")


def clear_cache():
    """Очистить кэш LLM-классификатора."""
    _classify_llm.cache_clear()
