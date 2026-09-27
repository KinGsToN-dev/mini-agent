"""Тесты для agent/history.py — JSONL-хранилище сообщений."""
import json
import pytest


class TestAppendMessage:

    @pytest.mark.unit
    def test_append_creates_file(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "привет")
        path = temp_session_dir / "test.jsonl"
        assert path.exists()

    @pytest.mark.unit
    def test_append_writes_json(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "привет")
        path = temp_session_dir / "test.jsonl"
        line = path.read_text(encoding="utf-8").strip()
        record = json.loads(line)
        assert record["role"] == "user"
        assert record["text"] == "привет"
        assert "ts" in record

    @pytest.mark.unit
    def test_append_multiple(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "1")
        history.append_message("test", "agent", "2")
        history.append_message("test", "user", "3")
        path = temp_session_dir / "test.jsonl"
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

    @pytest.mark.unit
    def test_empty_session_name(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("", "user", "test")


class TestLoadMessages:

    @pytest.mark.unit
    def test_load_empty(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        assert history.load_messages("missing") == []

    @pytest.mark.unit
    def test_load_after_append(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "a")
        history.append_message("test", "agent", "b")
        msgs = history.load_messages("test")
        assert len(msgs) == 2
        assert msgs[0]["text"] == "a"
        assert msgs[1]["role"] == "agent"

    @pytest.mark.unit
    def test_count_messages(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        for i in range(5):
            history.append_message("test", "user", f"msg{i}")
        assert history.count_messages("test") == 5


class TestFindInMessages:

    @pytest.mark.unit
    def test_find_found(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("s1", "user", "hello world")
        history.append_message("s1", "agent", "hi there")
        hits = history.find_in_messages("hello")
        assert len(hits) == 1
        assert hits[0]["session"] == "s1"

    @pytest.mark.unit
    def test_find_case_insensitive(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "Hello World")
        hits = history.find_in_messages("HELLO")
        assert len(hits) == 1

    @pytest.mark.unit
    def test_find_nothing(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "abc")
        hits = history.find_in_messages("xyz")
        assert len(hits) == 0


class TestClearMessages:

    @pytest.mark.unit
    def test_clear_removes_file(self, temp_session_dir, monkeypatch):
        monkeypatch.setattr("agent.history.SESSIONS_DIR", str(temp_session_dir))
        from agent import history
        history.append_message("test", "user", "abc")
        history.clear_messages("test")
        assert history.load_messages("test") == []