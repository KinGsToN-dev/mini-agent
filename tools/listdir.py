"""Инструмент list_dir — структурированный список файлов."""

import os
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 ** 3:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 ** 3):.2f} GB"


def _format_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%d.%m %H:%M")


def list_dir(path: str = ".", recursive: bool = False,
             pattern: str = None, max_items: int = 200) -> str:
    """Возвращает структурированный список файлов и папок."""
    try:
        base = Path(path).expanduser().resolve()
        if not base.exists():
            return f"[ERROR] Путь не найден: {path}"
        if not base.is_dir():
            return f"[ERROR] Это не директория: {path}"

        items = []
        if recursive:
            for root, dirs, files in os.walk(base):
                # Пропускаем служебные
                dirs[:] = [d for d in dirs
                           if d not in (".venv", "__pycache__", ".git", "node_modules")]
                for name in files:
                    if pattern and not fnmatch(name, pattern):
                        continue
                    full = Path(root) / name
                    try:
                        st = full.stat()
                        rel = full.relative_to(base)
                        items.append(("file", str(rel), st.st_size, st.st_mtime))
                    except Exception:
                        continue
        else:
            for entry in sorted(base.iterdir()):
                if entry.name in (".venv", "__pycache__", ".git"):
                    continue
                if pattern and not fnmatch(entry.name, pattern):
                    continue
                try:
                    st = entry.stat()
                    kind = "dir " if entry.is_dir() else "file"
                    size = 0 if entry.is_dir() else st.st_size
                    items.append((kind, entry.name, size, st.st_mtime))
                except Exception:
                    continue

        if not items:
            return f"(пусто: {base})"

        # Сортировка: файлы и папки вместе, по имени
        items.sort(key=lambda x: x[1].lower())
        items = items[:max_items]

        lines = [f"Содержимое {base}:"]
        total_size = 0
        for kind, name, size, mtime in items:
            if kind == "dir ":
                lines.append(f"  [DIR]  {name}/")
            else:
                total_size += size
                lines.append(f"         {name:<40} {_format_size(size):>10}  {_format_time(mtime)}")

        if len(items) >= max_items:
            lines.append(f"  ...[показано {max_items} из большего числа]")

        files_count = sum(1 for k, _, _, _ in items if k == "file")
        dirs_count = sum(1 for k, _, _, _ in items if k == "dir ")
        lines.append(f"\nИтого: {dirs_count} папок, {files_count} файлов, "
                     f"размер файлов: {_format_size(total_size)}")

        return "\n".join(lines)
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
