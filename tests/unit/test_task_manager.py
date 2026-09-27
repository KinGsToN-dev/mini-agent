"""Тесты для scripts/task_manager.py — с моками subprocess."""
from unittest.mock import MagicMock, patch

import pytest

# Импортируем модуль — там есть зависимость от PROJECT_DIR
# Не запускаем никаких команд — просто проверяем структуры
from scripts import task_manager


# ============================================================
# Реестр задач
# ============================================================

class TestTasksRegistry:

    @pytest.mark.unit
    def test_tasks_dict_has_briefing(self):
        assert "briefing" in task_manager.TASKS

    @pytest.mark.unit
    def test_tasks_dict_has_monitor(self):
        assert "monitor" in task_manager.TASKS

    @pytest.mark.unit
    def test_briefing_fields(self):
        b = task_manager.TASKS["briefing"]
        assert b["script"] == "daily_briefing.py"
        assert b["default_interval"] == "daily"
        assert b["default_time"] == "04:00"
        assert "name" in b

    @pytest.mark.unit
    def test_monitor_fields(self):
        m = task_manager.TASKS["monitor"]
        assert m["script"] == "position_monitor.py"
        assert m["default_interval"] == "hourly"

    @pytest.mark.unit
    def test_names_unique(self):
        names = [t["name"] for t in task_manager.TASKS.values()]
        assert len(names) == len(set(names)), "Имена задач должны быть уникальны"


# ============================================================
# get_task
# ============================================================

class TestGetTask:

    @pytest.mark.unit
    def test_get_existing(self):
        t = task_manager.get_task("briefing")
        assert t["script"] == "daily_briefing.py"

    @pytest.mark.unit
    def test_get_missing_exits(self):
        with pytest.raises(SystemExit):
            task_manager.get_task("nonexistent")


# ============================================================
# _run_schtasks
# ============================================================

class TestRunSchtasks:

    @pytest.mark.unit
    def test_success(self):
        with patch("scripts.task_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"ok", stderr=b"")
            code, out, err = task_manager._run_schtasks(["/Query"])
        assert code == 0

    @pytest.mark.unit
    def test_failure_prints_error(self, capsys):
        with patch("scripts.task_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")
            code, _, _ = task_manager._run_schtasks(["/Query"])
        assert code == 1


# ============================================================
# _task_exists
# ============================================================

class TestTaskExists:

    @pytest.mark.unit
    def test_exists(self):
        with patch("scripts.task_manager._run_schtasks") as mock:
            mock.return_value = (0, b"", b"")
            assert task_manager._task_exists("TestTask") is True

    @pytest.mark.unit
    def test_not_exists(self):
        with patch("scripts.task_manager._run_schtasks") as mock:
            mock.return_value = (1, b"", b"not found")
            assert task_manager._task_exists("TestTask") is False


# ============================================================
# Парсинг XML
# ============================================================

class TestReadTaskXml:

    @pytest.mark.unit
    def test_utf16_le_decode(self):
        xml = '<?xml version="1.0"?><Task><Settings/></Task>'
        # UTF-16-LE с BOM
        raw = b"\xff\xfe" + xml.encode("utf-16-le")

        with patch("scripts.task_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=raw, stderr=b"")
            result = task_manager._read_task_xml("TestTask")

        assert result is not None
        assert "<Task>" in result

    @pytest.mark.unit
    def test_returns_none_on_failure(self):
        with patch("scripts.task_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"")
            assert task_manager._read_task_xml("TestTask") is None


# ============================================================
# cmd_delete
# ============================================================

class TestCmdDelete:

    @pytest.mark.unit
    def test_nonexistent_task(self, capsys):
        args = MagicMock(task_name="briefing")
        with patch("scripts.task_manager._task_exists", return_value=False):
            task_manager.cmd_delete(args)
        captured = capsys.readouterr()
        assert "не существует" in captured.out

    @pytest.mark.unit
    def test_existing_task(self):
        args = MagicMock(task_name="briefing")
        with patch("scripts.task_manager._task_exists", return_value=True), \
             patch("scripts.task_manager._run_schtasks") as mock_run:
            mock_run.return_value = (0, b"", b"")
            task_manager.cmd_delete(args)
        # Проверяем, что вызвали /Delete
        call_args = mock_run.call_args[0][0]
        assert "/Delete" in call_args


# ============================================================
# cmd_enable / cmd_disable
# ============================================================

class TestCmdEnableDisable:

    @pytest.mark.unit
    def test_enable(self):
        args = MagicMock(task_name="briefing")
        with patch("scripts.task_manager._task_exists", return_value=True), \
             patch("scripts.task_manager._run_schtasks") as mock_run:
            mock_run.return_value = (0, b"", b"")
            task_manager.cmd_enable(args)
        call_args = mock_run.call_args[0][0]
        assert "/ENABLE" in call_args

    @pytest.mark.unit
    def test_disable(self):
        args = MagicMock(task_name="briefing")
        with patch("scripts.task_manager._task_exists", return_value=True), \
             patch("scripts.task_manager._run_schtasks") as mock_run:
            mock_run.return_value = (0, b"", b"")
            task_manager.cmd_disable(args)
        call_args = mock_run.call_args[0][0]
        assert "/DISABLE" in call_args