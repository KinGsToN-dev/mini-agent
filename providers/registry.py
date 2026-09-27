"""Реестр провайдеров и управление текущим."""

import os

from providers import groq as groq_mod
from providers import mistral as mistral_mod

_instances = {}


def get_provider(name: str):
    """Возвращает экземпляр провайдера (кэшируется)."""
    if name in _instances:
        return _instances[name]

    if name == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY не найден в .env")
        _instances[name] = groq_mod.create(api_key)
        return _instances[name]

    if name == "mistral":
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY не найден в .env")
        _instances[name] = mistral_mod.create(api_key)
        return _instances[name]

    if name == "gemini":
        # Gemini обрабатывается отдельно в agent/core.py
        return None

    raise ValueError(f"Неизвестный провайдер: {name}")


def available_providers() -> list:
    """Список доступных провайдеров (по наличию ключей в .env)."""
    result = []
    if os.getenv("GEMINI_API_KEY"):
        result.append("gemini")
    if os.getenv("GROQ_API_KEY"):
        result.append("groq")
    if os.getenv("MISTRAL_API_KEY"):
        result.append("mistral")
    return result
