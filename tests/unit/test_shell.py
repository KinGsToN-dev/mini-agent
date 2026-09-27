"""Тесты для tools/shell.py — классификация команд и безопасность."""
import pytest

from tools.shell import classify_command, is_dangerous_cmd


class TestClassifyCommand:

    @pytest.mark.unit
    @pytest.mark.parametrize("cmd", [
        "dir", "dir /w", "dir /b", "type file.txt", "echo hello", "echo.",
        "cd C:\\projects", "cd ..", "pwd", "where python", "whoami",
        "hostname", "ipconfig", "ipconfig /all", "systeminfo",
        "python --version", "python -V", "pip list", "pip show rich",
        "git status", "git log", "git log --oneline", "git diff", "git diff HEAD",
        "tasklist",
    ])
    def test_safe_commands(self, cmd):
        assert classify_command(cmd) == "safe", \
            f"'{cmd}' должен быть safe, но получил {classify_command(cmd)}"

    @pytest.mark.unit
    @pytest.mark.parametrize("cmd", [
        "format C:", "format /q D:", "FORMAT C:",
        "mkfs.ext4 /dev/sda1", "dd if=/dev/zero of=/dev/sda",
        "shutdown /s /t 0", "shutdown /r", "reboot", "diskpart",
        "del /s /q C:\\*", "rmdir /s /q C:\\Windows",
        "rm -rf /", "rm -rf ~",
        "reg delete HKLM\\Software\\Test", "reg delete HKCU\\Software\\Test",
    ])
    def test_blocked_commands(self, cmd):
        assert classify_command(cmd) == "blocked", \
            f"'{cmd}' должен быть blocked, но получил {classify_command(cmd)}"

    @pytest.mark.unit
    @pytest.mark.parametrize("cmd", [
        "python script.py", "pip install requests", "del file.txt",
        "copy a.txt b.txt", "mkdir new_folder", "git commit -m 'test'",
        "python -c 'print(1)'", "curl https://example.com",
        "npm install", "node server.js", "cargo build", "go run main.go",
    ])
    def test_ask_commands(self, cmd):
        assert classify_command(cmd) == "ask", \
            f"'{cmd}' должен быть ask, но получил {classify_command(cmd)}"

    @pytest.mark.unit
    def test_empty_command(self):
        assert classify_command("") == "ask"
        assert classify_command("   ") == "ask"

    @pytest.mark.unit
    def test_case_insensitive(self):
        assert classify_command("DIR") == "safe"
        assert classify_command("Dir") == "safe"
        assert classify_command("FORMAT C:") == "blocked"
        assert classify_command("Format C:") == "blocked"


class TestIsDangerous:

    @pytest.mark.unit
    @pytest.mark.parametrize("cmd", [
        "del /s file.txt", "del /q file.txt", "del /s /q file.txt",
        "rmdir /s /q folder", "rm -rf folder", "rm -r folder",
        "Remove-Item -Recurse folder", "Remove-Item -Force file",
        "cipher /w C:", "sfc /scannow", "chkdsk /f", "attrib -s -h file",
    ])
    def test_dangerous_commands(self, cmd):
        assert is_dangerous_cmd(cmd) is True, f"'{cmd}' должен быть dangerous"

    @pytest.mark.unit
    @pytest.mark.parametrize("cmd", [
        "dir", "python script.py", "echo hello", "pip install requests",
        "del file.txt", "rmdir folder", "git status", "type readme.md",
    ])
    def test_safe_not_dangerous(self, cmd):
        assert is_dangerous_cmd(cmd) is False, f"'{cmd}' НЕ должен быть dangerous"

    @pytest.mark.unit
    def test_empty(self):
        assert is_dangerous_cmd("") is False