"""AgentClient — HTTP-обёртка над agent_server."""

from typing import Optional

import httpx


DEFAULT_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT = 120.0  # 2 минуты — трейдинг + tool-chains могут долго


class AgentClientError(Exception):
    """Ошибка клиента (сеть, сервер, ответ)."""


class AgentClient:
    """HTTP-клиент для agent_server.

    Не имеет доступа к агенту напрямую — только через HTTP.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # --- Служебные ---

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Универсальный запрос. Возвращает JSON или бросает AgentClientError."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.request(method, self._url(path), **kwargs)
        except httpx.ConnectError as e:
            raise AgentClientError(
                f"Не могу подключиться к {self.base_url}\n"
                f"Запусти сервер: python scripts/run_agent_server.py\n"
                f"Детали: {e}"
            )
        except httpx.TimeoutException:
            raise AgentClientError(
                f"Таймаут {self.timeout}с — сервер не отвечает"
            )
        except httpx.HTTPError as e:
            raise AgentClientError(f"HTTP-ошибка: {e}")

        if r.status_code >= 400:
            # Пытаемся извлечь detail
            try:
                data = r.json()
                detail = data.get("detail", r.text)
            except Exception:
                detail = r.text
            raise AgentClientError(f"Сервер вернул {r.status_code}: {detail}")

        try:
            return r.json()
        except Exception:
            return {"raw": r.text}

    # --- /health ---

    def health(self) -> dict:
        return self._request("GET", "/health")

    def is_alive(self) -> bool:
        """Проверка доступности сервера. True/False, без исключений."""
        try:
            self.health()
            return True
        except AgentClientError:
            return False

    # --- /status ---

    def status(self) -> dict:
        return self._request("GET", "/status")

    # --- /ask ---

    def ask(self, text: str, session_id: str = "default") -> dict:
        return self._request(
            "POST",
            "/ask",
            json={"text": text, "session_id": session_id},
        )

    # --- /reset ---

    def reset(self, session_id: str = "default") -> dict:
        return self._request(
            "POST",
            "/reset",
            json={"session_id": session_id},
        )

    # --- /forget ---

    def forget(self) -> dict:
        return self._request("POST", "/forget")

    # --- /providers ---

    def providers(self) -> dict:
        return self._request("GET", "/providers")

    # --- /provider ---

    def switch_provider(self, provider: str, session_id: str = "default") -> dict:
        return self._request(
            "POST",
            "/provider",
            json={"provider": provider, "session_id": session_id},
        )

    # --- /model ---

    def switch_model(self, model: str, session_id: str = "default") -> dict:
        return self._request(
            "POST",
            "/model",
            json={"model": model, "session_id": session_id},
        )
