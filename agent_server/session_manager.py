"""Управление сессиями GeminiAgent.

Один агент на session_id. По умолчанию — сессия "default".
Агент — мультипровайдерный (Gemini/Groq/Mistral/OpenRouter)
с включённым роутером и fallback.
"""

import threading

from agent import GeminiAgent


DEFAULT_SESSION_ID = "default"
MAX_SESSIONS = 20


class SessionManager:
    """Пул сессий GeminiAgent, потокобезопасный."""

    def __init__(self, api_key: str, default_model_key: str = "lite-3.5"):
        self._api_key = api_key
        self._default_model_key = default_model_key
        self._sessions: dict[str, GeminiAgent] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str = DEFAULT_SESSION_ID) -> GeminiAgent:
        """Возвращает существующую сессию или создаёт новую."""
        session_id = session_id or DEFAULT_SESSION_ID

        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]

            if len(self._sessions) >= MAX_SESSIONS:
                raise RuntimeError(
                    f"Достигнут лимит сессий: {MAX_SESSIONS}. "
                    f"Сбрось старые через POST /reset."
                )

            agent = GeminiAgent(
                api_key=self._api_key,
                model_key=self._default_model_key,
            )
            # Как в REPL: роутер и авто-выбор модели включены
            agent.router_enabled = True
            agent.auto_route = True

            self._sessions[session_id] = agent
            return agent

    def reset(self, session_id: str = DEFAULT_SESSION_ID) -> bool:
        """Сбрасывает сессию (удаляет агента)."""
        session_id = session_id or DEFAULT_SESSION_ID
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def list_sessions(self) -> list:
        """Список активных session_id."""
        with self._lock:
            return list(self._sessions.keys())

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def clear_all(self):
        with self._lock:
            self._sessions.clear()
