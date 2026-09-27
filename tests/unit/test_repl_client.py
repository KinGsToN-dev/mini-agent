"""Тесты для repl_client — REPL-клиент через HTTP."""
from unittest.mock import MagicMock, patch

import httpx
import pytest

from repl_client.client import AgentClient, AgentClientError


@pytest.fixture
def client():
    return AgentClient(base_url="http://test.local", timeout=5.0)


def _mock_response(status=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


def _mock_client_ctx(response):
    """Возвращает мок httpx.Client как контекстный менеджер."""
    mock = MagicMock()
    mock.__enter__.return_value.request.return_value = response
    return mock


# ============================================================
# Базовые эндпоинты
# ============================================================

class TestHealth:

    @pytest.mark.unit
    def test_health_ok(self, client):
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, {"status": "ok"}))):
            r = client.health()
            assert r["status"] == "ok"

    @pytest.mark.unit
    def test_is_alive_true(self, client):
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, {"status": "ok"}))):
            assert client.is_alive() is True

    @pytest.mark.unit
    def test_is_alive_false_on_connect_error(self, client):
        with patch("repl_client.client.httpx.Client") as mock:
            mock.return_value.__enter__.return_value.request.side_effect = \
                httpx.ConnectError("connection refused")
            assert client.is_alive() is False


class TestStatus:

    @pytest.mark.unit
    def test_status(self, client):
        data = {"provider": "gemini", "model": "gemini-3.5-flash-lite", "mode": "ask"}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.status()
            assert r["provider"] == "gemini"
            assert r["model"] == "gemini-3.5-flash-lite"


# ============================================================
# Ask
# ============================================================

class TestAsk:

    @pytest.mark.unit
    def test_ask_returns_answer(self, client):
        data = {"answer": "Привет!", "provider": "groq", "model": "gpt-oss-20b",
                "duration_ms": 1234}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.ask("привет")
            assert r["answer"] == "Привет!"
            assert r["duration_ms"] == 1234

    @pytest.mark.unit
    def test_ask_sends_post(self, client):
        with patch("repl_client.client.httpx.Client") as mock_cls:
            mock_ctx = mock_cls.return_value.__enter__.return_value
            mock_ctx.request.return_value = _mock_response(200, {"answer": "ok"})
            client.ask("hello", session_id="s1")
            call_args = mock_ctx.request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1].endswith("/ask")
            assert call_args[1]["json"]["text"] == "hello"
            assert call_args[1]["json"]["session_id"] == "s1"


# ============================================================
# Ошибки
# ============================================================

class TestErrors:

    @pytest.mark.unit
    def test_connect_error_raises_agent_client_error(self, client):
        with patch("repl_client.client.httpx.Client") as mock:
            mock.return_value.__enter__.return_value.request.side_effect = \
                httpx.ConnectError("refused")
            with pytest.raises(AgentClientError) as exc_info:
                client.status()
            assert "Не могу подключиться" in str(exc_info.value)

    @pytest.mark.unit
    def test_timeout_raises(self, client):
        with patch("repl_client.client.httpx.Client") as mock:
            mock.return_value.__enter__.return_value.request.side_effect = \
                httpx.TimeoutException("timeout")
            with pytest.raises(AgentClientError) as exc_info:
                client.status()
            assert "Таймаут" in str(exc_info.value)

    @pytest.mark.unit
    def test_http_400_raises_with_detail(self, client):
        resp = _mock_response(400, {"detail": "Пустой текст"})
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(resp)):
            with pytest.raises(AgentClientError) as exc_info:
                client.ask("")
            assert "400" in str(exc_info.value)
            assert "Пустой" in str(exc_info.value)

    @pytest.mark.unit
    def test_http_500_raises(self, client):
        resp = _mock_response(500, {"detail": "Внутренняя ошибка"})
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(resp)):
            with pytest.raises(AgentClientError):
                client.ask("test")


# ============================================================
# Управление
# ============================================================

class TestSwitching:

    @pytest.mark.unit
    def test_switch_provider(self, client):
        data = {"status": "ok", "provider": "groq", "model": "gpt-oss-20b"}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.switch_provider("groq")
            assert r["provider"] == "groq"

    @pytest.mark.unit
    def test_switch_model(self, client):
        data = {"status": "ok", "model": "gpt-oss-120b"}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.switch_model("gpt-oss-120b")
            assert r["model"] == "gpt-oss-120b"

    @pytest.mark.unit
    def test_providers(self, client):
        data = {"current": "gemini", "providers": [
            {"name": "gemini", "available": True, "is_current": True},
            {"name": "groq", "available": True, "is_current": False},
        ]}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.providers()
            assert r["current"] == "gemini"
            assert len(r["providers"]) == 2

    @pytest.mark.unit
    def test_reset(self, client):
        data = {"status": "ok", "session_id": "default", "existed": True}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.reset()
            assert r["existed"] is True

    @pytest.mark.unit
    def test_forget(self, client):
        data = {"status": "ok", "cleared_sessions": 1}
        with patch("repl_client.client.httpx.Client",
                   return_value=_mock_client_ctx(_mock_response(200, data))):
            r = client.forget()
            assert r["cleared_sessions"] == 1


# ============================================================
# Конструктор
# ============================================================

class TestInit:

    @pytest.mark.unit
    def test_default_url(self):
        c = AgentClient()
        assert c.base_url == "http://127.0.0.1:8765"

    @pytest.mark.unit
    def test_strips_trailing_slash(self):
        c = AgentClient(base_url="http://localhost:8765/")
        assert c.base_url == "http://localhost:8765"

    @pytest.mark.unit
    def test_custom_timeout(self):
        c = AgentClient(timeout=30.0)
        assert c.timeout == 30.0
