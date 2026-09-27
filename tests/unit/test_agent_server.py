"""Тесты для agent_server — скелет (Этап 1.1)."""
import pytest
from fastapi.testclient import TestClient

from agent_server.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:

    @pytest.mark.unit
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    @pytest.mark.unit
    def test_health_version_format(self, client):
        r = client.get("/health")
        data = r.json()
        # Версия формата X.Y.Z
        parts = data["version"].split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestStatus:

    @pytest.mark.unit
    def test_status_ok(self, client):
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "provider" in data
        assert "model" in data
        assert "mode" in data

    @pytest.mark.unit
    def test_status_stub_values(self, client):
        """Этап 1.1 — заглушка."""
        r = client.get("/status")
        data = r.json()
        assert data["model"] == "not-connected-yet"


class TestAsk:

    @pytest.mark.unit
    def test_ask_returns_answer(self, client):
        r = client.post("/ask", json={"text": "привет"})
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "привет" in data["answer"]

    @pytest.mark.unit
    def test_ask_stub_marker(self, client):
        """Этап 1.1 — заглушка."""
        r = client.post("/ask", json={"text": "test"})
        data = r.json()
        assert "[NOT IMPLEMENTED]" in data["answer"]

    @pytest.mark.unit
    def test_ask_empty_text_rejected(self, client):
        """Пустой текст — 422 от pydantic (min_length=1)."""
        r = client.post("/ask", json={"text": ""})
        assert r.status_code in (400, 422)

    @pytest.mark.unit
    def test_ask_missing_text_rejected(self, client):
        r = client.post("/ask", json={})
        assert r.status_code == 422

    @pytest.mark.unit
    def test_ask_default_session(self, client):
        r = client.post("/ask", json={"text": "test"})
        data = r.json()
        assert data["provider"] == "stub"
        assert data["model"] == "stub"

    @pytest.mark.unit
    def test_ask_custom_session(self, client):
        r = client.post(
            "/ask",
            json={"text": "test", "session_id": "my_session"},
        )
        data = r.json()
        assert "my_session" in data["answer"]

    @pytest.mark.unit
    def test_ask_too_long_rejected(self, client):
        """Текст > 10 000 символов — 422."""
        long_text = "x" * 10_001
        r = client.post("/ask", json={"text": long_text})
        assert r.status_code == 422


class TestRoot:

    @pytest.mark.unit
    def test_root_lists_endpoints(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "endpoints" in data
        assert "/health" in data["endpoints"]
        assert "/ask" in data["endpoints"]

    @pytest.mark.unit
    def test_404_for_unknown_path(self, client):
        r = client.get("/nonexistent")
        assert r.status_code == 404
