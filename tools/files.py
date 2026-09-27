"""read_file / write_file."""

from pathlib import Path


def read_file(path: str) -> str:
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"[ERROR] Файл не найден: {path}"
        if not p.is_file():
            return f"[ERROR] Это не файл: {path}"
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > 8000:
            content = content[:8000] + "\n...[обрезано]"
        return content
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


def write_file(path: str, content: str) -> str:
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"[OK] Записано {len(content)} символов в {p}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
