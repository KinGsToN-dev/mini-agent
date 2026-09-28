"""run_shell с проверкой безопасности и режимами ask/auto/dry."""

import subprocess
import os
import re
from datetime import datetime

TIMEOUT_SECONDS = 30
LOG_FILE = "agent.log"

# Команды, запрещённые навсегда (даже с подтверждением)
# Команды, запрещённые навсегда (даже с подтверждением)
BLOCKED_PATTERNS = [
    # Форматирование / низкоуровневые операции
    r"\bformat\b", r"\bmkfs\b", r"\bdd\s+if=", r":\(\)\s*\{",
    r"\bshutdown\b", r"\breboot\b", r"\bdiskpart\b",

    # Рекурсивное удаление с корня или пользовательских папок
    # Ловим и "C:\" в конце, и "C:\*", и "C:\Windows"
    r"\bdel\s+/[sq].*[a-zA-Z]:\\",
    r"\brmdir\s+/[sq].*[a-zA-Z]:\\",
    r"\brm\s+-rf\s+/", r"\brm\s+-rf\s+~",

    # PowerShell-эквиваленты рекурсивного удаления
    r"Remove-Item\s+.*-Recurse\s+.*-Force",
    r"Remove-Item\s+.*-Force\s+.*-Recurse",

    # Реестр Windows
    r"\breg\s+delete\b",
    r"Remove-ItemProperty\s+.*HKLM",
    r"Remove-ItemProperty\s+.*HKCU",

    # Опасные сочетания (рекурсивное удаление из текущей папки)
    r"\bdel\s+/s\s+/q\s+\*\.",
    r"\bdel\s+/q\s+/s\s+\*\.",
]
# Паттерны, требующие ДОПОЛНИТЕЛЬНОГО подтверждения (даже в auto-режиме)
DANGEROUS_PATTERNS = [
    r"\bdel\s+/[sq]",         # удаление с ключами
    r"\brmdir\s+/[sq]",       # удаление папки с ключами
    r"\brm\s+-rf?\b",         # rm -r / rm -rf
    r"\bRemove-Item\b.*-Recurse",
    r"\bRemove-Item\b.*-Force",
    r"\bcipher\s+/w",         # затирание свободного места
    r"\bsfc\s+/scannow",      # проверка системы (долго)
    r"\bchkdsk\b.*\/f",       # проверка диска (может изменить)
    r"\battrib\b.*-s\s+-h",   # снятие системных/скрытых атрибутов
]


def is_dangerous_cmd(command: str) -> bool:
    """Проверяет, попадает ли команда в список 'опасных'."""
    for pat in DANGEROUS_PATTERNS:
        if re.search(pat, command, flags=re.IGNORECASE):
            return True
    return False

SAFE_PATTERNS = [
    r"^dir\b", r"^type\b", r"^echo\b", r"^cd\b", r"^pwd\b",
    r"^where\b", r"^whoami\b", r"^hostname\b", r"^ipconfig\b",
    r"^systeminfo\b", r"^python\s+--version\b", r"^python\s+-V\b",
    r"^pip\s+list\b", r"^pip\s+show\b", r"^git\s+status\b",
    r"^git\s+log\b", r"^git\s+diff\b", r"^tasklist\b",
]

_state = {"mode": "ask", "confirm_callback": None}


def classify_command(command: str) -> str:
    cmd = command.strip().lower()
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            return "blocked"
    for pat in SAFE_PATTERNS:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            return "safe"
    return "ask"


def set_mode(mode: str):
    if mode not in ("ask", "auto", "dry"):
        raise ValueError(f"Неверный режим: {mode}")
    _state["mode"] = mode


def get_mode() -> str:
    return _state["mode"]


def set_confirm_callback(cb):
    _state["confirm_callback"] = cb


def log_event(kind: str, message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{kind}] {message}\n")
    except Exception:
        pass


def _decode(raw: bytes) -> str:
    if not raw:
        return ""
    if os.name == "nt":
        for enc in ("cp866", "cp1251", "utf-8"):
            try:
                return raw.decode(enc).replace("\xa0", " ")
            except UnicodeDecodeError:
                continue
        from agent.log import log
        log("shell: fallback decode cp866", level="DEBUG")
        return raw.decode("cp866", errors="replace").replace("\xa0", " ")
    return raw.decode("utf-8", errors="replace")


def run_shell(command: str) -> str:
    kind = classify_command(command)
    mode = _state["mode"]
    log_event("SHELL", f"mode={mode} kind={kind} cmd={command!r}")

    if kind == "blocked":
        log_event("BLOCKED", command)
        return f"[BLOCKED] Команда запрещена навсегда: {command}"

    if mode == "dry":
        log_event("DRY", command)
        return f"[DRY-RUN] Команда не выполнена (режим dry): {command}"

    # Дополнительная защита: опасные команды требуют подтверждения ВСЕГДА
    is_dangerous = is_dangerous_cmd(command)

    if is_dangerous and mode != "dry":
        # Даже в auto — спрашиваем
        cb = _state["confirm_callback"]
        if cb is None:
            return f"[BLOCKED] Опасная команда, нет обработчика подтверждения: {command}"
        log_event("DANGEROUS", command)
        allowed = cb(command, dangerous=True)
        log_event("CONFIRM_DANGEROUS", f"allowed={allowed} cmd={command!r}")
        if not allowed:
            return f"[DENIED] Пользователь отклонил опасную команду: {command}"
    elif mode == "ask" and kind == "ask":
        cb = _state["confirm_callback"]
        if cb is None:
            return f"[BLOCKED] Нет обработчика подтверждения: {command}"
        allowed = cb(command)
        log_event("CONFIRM", f"allowed={allowed} cmd={command!r}")
        if not allowed:
            return f"[DENIED] Пользователь отклонил: {command}"

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            timeout=TIMEOUT_SECONDS, cwd=os.getcwd(),
        )
        output = _decode(result.stdout)
        stderr = _decode(result.stderr)
        if stderr:
            output += ("\n[stderr]\n" if output else "[stderr]\n") + stderr
        if not output.strip():
            output = f"(код {result.returncode}, пустой вывод)"
        if len(output) > 8000:
            output = output[:8000] + "\n...[обрезано]"
        log_event("RESULT", f"rc={result.returncode} len={len(output)}")
        return output
    except subprocess.TimeoutExpired:
        return f"[ERROR] Таймаут {TIMEOUT_SECONDS}с"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"

