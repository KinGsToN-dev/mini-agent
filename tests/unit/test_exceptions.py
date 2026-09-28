"""Тесты для agent/exceptions.py и agent/log.py."""
from unittest.mock import patch, mock_open
from pathlib import Path

import pytest

from agent import exceptions
from agent import log as log_mod


# ============================================================
# Исключения
# ============================================================

class TestExceptionsHierarchy:

    @pytest.mark.unit
    def test_all_inherit_from_agent_error(self):
        """Все кастомные ошибки наследуются от AgentError."""
        for cls in (
            exceptions.MT5Error,
            exceptions.TradingViewError,
            exceptions.TelegramError,
            exceptions.ProviderError,
            exceptions.ToolError,
            exceptions.ConfigError,
        ):
            assert issubclass(cls, exceptions.AgentError), \
                f"{cls.__name__} должен наследоваться от AgentError"

    @pytest.mark.unit
    def test_agent_error_inherits_from_exception(self):
        assert issubclass(exceptions.AgentError, Exception)

    @pytest.mark.unit
    def test_raise_and_catch(self):
        """Можно поймать MT5Error конкретно."""
        with pytest.raises(exceptions.MT5Error):
            raise exceptions.MT5Error("initialize failed")

    @pytest.mark.unit
    def test_catch_as_agent_error(self):
        """MT5Error ловится как AgentError."""
        with pytest.raises(exceptions.AgentError):
            raise exceptions.MT5Error("test")

    @pytest.mark.unit
    def test_error_message_preserved(self):
        err = exceptions.TradingViewError("CDP not responding")
        assert "CDP not responding" in str(err)

    @pytest.mark.unit
    def test_all_exceptions_distinct(self):
        """Каждый тип — отдельный класс, не алиас."""
        types = [
            exceptions.MT5Error,
            exceptions.TradingViewError,
            exceptions.TelegramError,
            exceptions.ProviderError,
            exceptions.ToolError,
            exceptions.ConfigError,
        ]
        assert len(set(types)) == len(types)


# ============================================================
# Логгер
# ============================================================

class TestLog:

    @pytest.mark.unit
    def test_log_writes_to_file(self, tmp_path, monkeypatch):
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))

        log_mod.log("test message")

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "test message" in content
        assert "[INFO]" in content

    @pytest.mark.unit
    def test_log_levels(self, tmp_path, monkeypatch):
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))
        monkeypatch.setattr(log_mod, "_DEFAULT_LEVEL", "DEBUG")

        log_mod.log("debug msg", level="DEBUG")
        log_mod.log("info msg", level="INFO")
        log_mod.log("warning msg", level="WARNING")
        log_mod.log("error msg", level="ERROR")

        content = log_file.read_text(encoding="utf-8")
        assert "[DEBUG] debug msg" in content
        assert "[INFO] info msg" in content
        assert "[WARNING] warning msg" in content
        assert "[ERROR] error msg" in content

    @pytest.mark.unit
    def test_shortcuts(self, tmp_path, monkeypatch):
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))
        monkeypatch.setattr(log_mod, "_DEFAULT_LEVEL", "DEBUG")

        log_mod.debug("d")
        log_mod.info("i")
        log_mod.warning("w")
        log_mod.error("e")

        content = log_file.read_text(encoding="utf-8")
        assert "[DEBUG] d" in content
        assert "[INFO] i" in content
        assert "[WARNING] w" in content
        assert "[ERROR] e" in content

    @pytest.mark.unit
    def test_level_filter(self, tmp_path, monkeypatch):
        """Если _DEFAULT_LEVEL=WARNING, то DEBUG/INFO не пишутся."""
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))
        monkeypatch.setattr(log_mod, "_DEFAULT_LEVEL", "WARNING")

        log_mod.log("info msg", level="INFO")
        log_mod.log("warning msg", level="WARNING")

        content = log_file.read_text(encoding="utf-8")
        assert "info msg" not in content
        assert "warning msg" in content

    @pytest.mark.unit
    def test_invalid_level_falls_back_to_info(self, tmp_path, monkeypatch):
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))

        log_mod.log("test", level="INVALID")

        content = log_file.read_text(encoding="utf-8")
        assert "[INFO]" in content

    @pytest.mark.unit
    def test_log_does_not_crash_on_io_error(self, monkeypatch):
        """Если файл недоступен — просто игнорируем."""
        monkeypatch.setattr(log_mod, "LOG_FILE", "Z:\\nonexistent\\path\\agent.log")
        # Не должно бросить
        log_mod.log("test")

    @pytest.mark.unit
    def test_timestamp_present(self, tmp_path, monkeypatch):
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))

        log_mod.log("test")

        content = log_file.read_text(encoding="utf-8")
        # Формат: [YYYY-MM-DD HH:MM:SS] [INFO] test
        assert content.startswith("[")
        assert "]" in content
        # Должен быть год 20XX
        assert "20" in content[:10]

    @pytest.mark.unit
    def test_appends_not_overwrites(self, tmp_path, monkeypatch):
        log_file = tmp_path / "agent_test.log"
        monkeypatch.setattr(log_mod, "LOG_FILE", str(log_file))

        log_mod.log("first")
        log_mod.log("second")

        content = log_file.read_text(encoding="utf-8")
        assert "first" in content
        assert "second" in content
        # Оба сообщения на месте, ни одно не перезаписано
        assert content.count("first") == 1
        assert content.count("second") == 1
