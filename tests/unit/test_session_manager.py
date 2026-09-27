"""Тесты для agent_server.session_manager — все с моками GeminiAgent."""
from unittest.mock import MagicMock, patch

import pytest

from agent_server.session_manager import (
    DEFAULT_SESSION_ID,
    MAX_SESSIONS,
    SessionManager,
)


@pytest.fixture
def mock_agent_class():
    """Мокаем GeminiAgent — каждый вызов возвращает НОВЫЙ мок."""
    with patch("agent_server.session_manager.GeminiAgent") as mock:
        mock.side_effect = lambda *a, **kw: MagicMock()
        yield mock


class TestSessionManager:

    @pytest.mark.unit
    def test_default_session_created(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        agent = sm.get_or_create(DEFAULT_SESSION_ID)
        assert agent is not None
        assert sm.count() == 1

    @pytest.mark.unit
    def test_get_or_create_reuses(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        a1 = sm.get_or_create("session_a")
        a2 = sm.get_or_create("session_a")
        assert a1 is a2
        assert sm.count() == 1

    @pytest.mark.unit
    def test_two_different_sessions(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        a1 = sm.get_or_create("s1")
        a2 = sm.get_or_create("s2")
        assert a1 is not a2
        assert sm.count() == 2

    @pytest.mark.unit
    def test_empty_session_id_uses_default(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        a1 = sm.get_or_create("")
        a2 = sm.get_or_create(DEFAULT_SESSION_ID)
        assert a1 is a2

    @pytest.mark.unit
    def test_reset_removes_session(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        sm.get_or_create("s1")
        existed = sm.reset("s1")
        assert existed is True
        assert sm.count() == 0

    @pytest.mark.unit
    def test_reset_nonexistent(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        existed = sm.reset("nope")
        assert existed is False

    @pytest.mark.unit
    def test_list_sessions(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        sm.get_or_create("a")
        sm.get_or_create("b")
        sm.get_or_create("c")
        assert sorted(sm.list_sessions()) == ["a", "b", "c"]

    @pytest.mark.unit
    def test_max_sessions_limit(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        for i in range(MAX_SESSIONS):
            sm.get_or_create(f"s{i}")
        with pytest.raises(RuntimeError) as exc_info:
            sm.get_or_create("overflow")
        assert "лимит" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_clear_all(self, mock_agent_class):
        sm = SessionManager(api_key="test_key")
        sm.get_or_create("a")
        sm.get_or_create("b")
        sm.clear_all()
        assert sm.count() == 0

    @pytest.mark.unit
    def test_agent_configuration(self, mock_agent_class):
        """При создании агента выставляются router_enabled, auto_route."""
        sm = SessionManager(api_key="test_key")
        agent = sm.get_or_create("s1")
        assert agent.router_enabled is True
        assert agent.auto_route is True
