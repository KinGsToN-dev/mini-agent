"""Инструмент grep — поиск текста в файлах (regex)."""

import os
import re
from pathlib import Path
from fnmatch import fnmatch

SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules", ".idea", ".vscode"}
SKIP_EXTS = {".pyc", ".pyo", ".exe", ".dll", ".so", ".bin", ".zip",
             ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".mp3", ".mp4", ".wav"}


def grep(pattern: str, path: str = ".", file_pattern: str = None,
         max_results: int = 50, context_lines: int = 0) -> str:
    """Ищет регулярное выражение pattern в файлах."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"[ERROR] Неверное регулярное выражение: {e}"

    try:
        base = Path(path).expanduser().resolve()
        if not base.exists():
            return f"[ERROR] Путь не найден: {path}"

        results = []
        files_scanned = 0

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext in SKIP_EXTS:
                    continue
                if file_pattern and not fnmatch(name, file_pattern):
                    continue

                full = Path(root) / name
                files_scanned += 1
                try:
                    with open(full, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue

                for i, line in enumerate(lines, 1):
                    if regex.search(line):
                        rel = full.relative_to(base)
                        text = line.rstrip()
                        if len(text) > 200:
                            text = text[:200] + "..."
                        results.append(f"  {rel}:{i}: {text}")
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        if not results:
            return f"Ничего не найдено. Просканировано файлов: {files_scanned}"

        header = f"Найдено совпадений: {len(results)} (в {files_scanned} файлах)"
        if len(results) >= max_results:
            header += f" [лимит {max_results} достигнут]"
        return header + "\n" + "\n".join(results)
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
