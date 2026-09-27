"""Тесты для agent_server — Этап 1.2 (с моками агента)."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agent_server.app import app


@pytest.fixture
def mock_agent():
    """Мок GeminiAgent."""
    agent = MagicMock()
    agent.ask.return_value = "Тестовый ответ агента"
    agent.provider_name = "test_provider"
    agent.model_name = "test_model"
    agent.router_enabled = True
    agent.auto_route = True
    agent.exhausted = set()
    return agent


@pytest.fixture
def mock_sm(mock_agent):
    """Мок SessionManager."""
    sm = MagicMock()
    sm.get_or_create.return_value = mock_agent
    sm.reset.return_value = True
    sm.list_sessions.return_value = ["default"]
    sm.count.return_value = 1
    return sm


@pytest.fixture
def client(mock_sm):
    """TestClient с подменённым SessionManager."""
    with patch("agent_server.app._session_manager", mock_sm):
        with patch("agent_server.app._get_session_manager", return_value=mock_sm):
            yield TestClient(app)


# ============================================================
# Health / Status
# ============================================================

class TestHealth:

    @pytest.mark.unit
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestStatus:

    @pytest.mark.unit
    def test_status_shows_real_agent(self, client, mock_agent):
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "test_provider"
        assert data["model"] == "test_model"
        assert data["router_enabled"] is True


# ============================================================
# Ask
# ============================================================

class TestAsk:

    @pytest.mark.unit
    def test_ask_calls_agent(self, client, mock_agent):
        r = client.post("/ask", json={"text": "привет"})
        assert r.status_code == 200
        data = r.json()
        assert data["answer"] == "Тестовый ответ агента"
        assert data["provider"] == "test_provider"
        mock_agent.ask.assert_called_once_with("привет")

    @pytest.mark.unit
    def test_ask_empty_text(self, client):
        r = client.post("/ask", json={"text": ""})
        assert r.status_code in (400, 422)

    @pytest.mark.unit
    def test_ask_agent_error_500(self, client, mock_agent):
        mock_agent.ask.side_effect = RuntimeError("Тестовая ошибка агента")
        r = client.post("/ask", json={"text": "test"})
        assert r.status_code == 500
        assert "Тестовая ошибка" in r.json()["detail"]


# ============================================================
# Reset / Forget
# ============================================================

class TestReset:

    @pytest.mark.unit
    def test_reset_calls_sm(self, client, mock_sm):
        r = client.post("/reset", json={"session_id": "default"})
        assert r.status_code == 200
        mock_sm.reset.assert_called_once_with("default")


class TestForget:

    @pytest.mark.unit
    def test_forget_clears(self, client, mock_sm, mock_agent):
        r = client.post("/forget")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"


# ============================================================
# Providers / Provider / Model
# ============================================================

class TestProviders:

    @pytest.mark.unit
    def test_providers_listed(self, client):
        with patch("providers.registry.available_providers", return_value=["gemini", "groq"]):
            r = client.get("/providers")
            assert r.status_code == 200
            data = r.json()
            assert "current" in data
            assert len(data["providers"]) == 4

    @pytest.mark.unit
    def test_switch_provider(self, client, mock_agent):
        mock_agent.switch_provider.return_value = ("groq", "gpt-oss-20b")
        r = client.post("/provider", json={"provider": "groq"})
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "groq"
        assert data["model"] == "gpt-oss-20b"

    @pytest.mark.unit
    def test_switch_model(self, client, mock_agent):
        mock_agent.switch_model.return_value = "gpt-oss-120b"
        r = client.post("/model", json={"model": "gpt-oss-120b"})
        assert r.status_code == 200
        data = r.json()
        assert data["model"] == "gpt-oss-120b"


# ============================================================
# Root
# ============================================================

class TestRoot:

    @pytest.mark.unit
    def test_root_endpoints(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        for ep in ["/health", "/ask", "/reset", "/forget", "/providers"]:
            assert ep in data["endpoints"]

    @pytest.mark.unit
    def test_404(self, client):
        r = client.get("/nonexistent")
        assert r.status_code == 404
