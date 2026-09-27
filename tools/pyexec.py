"""Инструмент python_exec — выполнение Python-кода в песочнице."""

import re
import subprocess
import os

TIMEOUT_SECONDS = 30
CONTEXT_LIMIT = 8000

# Запрещённые модули (импорт через import или from ... import)
BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "ctypes",
    "pty", "multiprocessing", "threading", "asyncio",
    "importlib", "builtins", "gc", "inspect", "pickle",
    "marshal", "shelve", "dbm", "sqlite3", "tempfile",
    "pathlib", "glob", "fnmatch", "stat", "fileinput",
    "signal", "resource", "platform", "getpass", "pwd",
    "grp", "atexit", "traceback", "warnings", "logging",
}

# Запрещённые имена/вызовы (regex)
BLOCKED_PATTERNS = [
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\b__import__\s*\(",
    r"\bopen\s*\(",        # запрещаем открытие файлов напрямую
    r"\bglobals\s*\(",
    r"\blocals\s*\(",
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
    r"\bdelattr\s*\(",
    r"__globals__",
    r"__builtins__",
    r"__subclasses__",
    r"__bases__",
    r"__class__",
    r"__mro__",
    r"\.\.",              # попытки обхода путей
]


def _analyze_code(code: str) -> str | None:
    """Статический анализ. Возвращает причину блокировки или None."""
    # Проверка импортов
    import_patterns = [
        r"^\s*import\s+(\w+)",
        r"^\s*from\s+(\w+)\s+import",
    ]
    for line in code.split("\n"):
        for pat in import_patterns:
            m = re.match(pat, line)
            if m:
                mod = m.group(1).lower()
                if mod in BLOCKED_MODULES:
                    return f"Запрещённый импорт: {mod}"

    # Проверка запрещённых вызовов
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, code):
            return f"Запрещённая конструкция: {pat}"

    return None


def python_exec(code: str, timeout: int = TIMEOUT_SECONDS,
                cwd: str = None) -> str:
    """Выполняет Python-код в отдельном процессе."""
    if not code or not code.strip():
        return "[ERROR] Пустой код"

    # Статический анализ
    reason = _analyze_code(code)
    if reason:
        return f"[BLOCKED] {reason}"

    try:
        result = subprocess.run(
            ["python", "-c", code],
            shell=False,
            capture_output=True,
            timeout=timeout,
            cwd=cwd or os.getcwd(),
        )

        def decode(raw):
            if not raw:
                return ""
            for enc in ("utf-8", "cp866", "cp1251"):
                try:
                    return raw.decode(enc).replace("\xa0", " ")
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")

        stdout = decode(result.stdout)
        stderr = decode(result.stderr)

        parts = [f"Код возврата: {result.returncode}"]
        if stdout:
            out = stdout if len(stdout) <= CONTEXT_LIMIT else stdout[:CONTEXT_LIMIT] + "\n...[обрезано]"
            parts.append(f"\nstdout:\n{out}")
        if stderr:
            err = stderr if len(stderr) <= CONTEXT_LIMIT else stderr[:CONTEXT_LIMIT] + "\n...[обрезано]"
            parts.append(f"\nstderr:\n{err}")
        if not stdout and not stderr:
            parts.append("(нет вывода)")

        return "\n".join(parts)

    except subprocess.TimeoutExpired:
        return f"[ERROR] Таймаут {timeout}с — код выполняется слишком долго"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
