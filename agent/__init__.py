"""Пакет агента.

FIX: GeminiAgent импортируется лениво (PEP 562), чтобы избежать
circular import при `from agent.log import log` из tools/*.
"""

from . import sessions
from . import analytics
from . import schemas

__all__ = ["GeminiAgent", "sessions", "analytics", "schemas"]


def __getattr__(name):
    if name == "GeminiAgent":
        from .core import GeminiAgent
        return GeminiAgent
    raise AttributeError(f"module 'agent' has no attribute {name!r}")