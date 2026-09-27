"""Тесты для tools/pyexec.py — блокировка опасного кода."""
import pytest

from tools.pyexec import python_exec, _analyze_code


class TestBlockedImports:

    @pytest.mark.unit
    @pytest.mark.parametrize("code", [
        "import os",
        "import os; os.system('dir')",
        "from os import system",
        "import subprocess",
        "import shutil",
        "import sys",
        "import socket",
        "import ctypes",
        "import pickle",
        "import sqlite3",
        "import pathlib",
    ])
    def test_blocked_modules(self, code):
        result = python_exec(code)
        assert "[BLOCKED]" in result, f"'{code}' должен быть заблокирован"

    @pytest.mark.unit
    @pytest.mark.parametrize("code", [
        "import math; print(math.pi)",
        "import json; print(json.dumps({}))",
        "import re; print(re.findall(r'\\\\d+', 'abc123'))",
        "import random; print(random.randint(1, 10))",
        "import datetime; print(datetime.date.today().year)",
        "import string; print(string.ascii_lowercase)",
    ])
    def test_safe_modules(self, code):
        result = python_exec(code)
        assert "[BLOCKED]" not in result


class TestBlockedFunctions:

    @pytest.mark.unit
    @pytest.mark.parametrize("code", [
        "eval('1+1')",
        "exec('print(1)')",
        "compile('x=1', '<s>', 'exec')",
        "__import__('os')",
        "open('file.txt')",
        "globals()",
        "locals()",
        "getattr(object, '__class__')",
    ])
    def test_blocked_functions(self, code):
        result = python_exec(code)
        assert "[BLOCKED]" in result


class TestSuccessfulExecution:

    @pytest.mark.unit
    def test_simple_print(self):
        result = python_exec("print(2 + 2)")
        assert "4" in result
        assert "Код возврата: 0" in result

    @pytest.mark.unit
    def test_stderr(self):
        result = python_exec("raise ValueError('test error')")
        assert "ValueError" in result

    @pytest.mark.unit
    def test_empty_code(self):
        result = python_exec("")
        assert "[ERROR]" in result


class TestAnalyzeCode:

    @pytest.mark.unit
    def test_analyze_safe(self):
        assert _analyze_code("print(1)") is None

    @pytest.mark.unit
    def test_analyze_blocked_import(self):
        reason = _analyze_code("import os")
        assert reason is not None
        assert "os" in reason

    @pytest.mark.unit
    def test_analyze_blocked_eval(self):
        reason = _analyze_code("eval('1')")
        assert reason is not None