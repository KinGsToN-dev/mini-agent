"""Общие фикстуры для тестов."""
import sys
import tempfile
import shutil
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp(prefix="mini_agent_test_")
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_session_dir(temp_dir, monkeypatch):
    sessions_dir = temp_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("agent.history.SESSIONS_DIR", str(sessions_dir))
    monkeypatch.setattr("agent.sessions.SESSIONS_DIR", str(sessions_dir))
    yield sessions_dir


@pytest.fixture
def isolated_agent_state(temp_dir, monkeypatch):
    state_file = temp_dir / "agent_state.json"
    monkeypatch.setattr("agent.state.STATE_FILE", str(state_file))
    yield state_file


@pytest.fixture
def clean_env(monkeypatch):
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "MISTRAL_API_KEY", "TAVILY_API_KEY"):
        monkeypatch.delenv(key, raising=False)