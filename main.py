"""
Мини-агент на Gemini. Точка входа.
"""

import os
import sys
from dotenv import load_dotenv

from repl.loop import run_repl


def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Ошибка: не найден GEMINI_API_KEY в .env")
        sys.exit(1)
    run_repl(api_key)


if __name__ == "__main__":
    main()
