"""
Мини-агент через HTTP-сервер. Точка входа клиента.

Требует запущенного сервера:
    python scripts/run_agent_server.py

Использование:
    python main_client.py
"""

import os
import sys

from repl_client.loop import run_client_repl


DEFAULT_URL = "http://127.0.0.1:8765"


def main():
    base_url = os.getenv("AGENT_SERVER_URL", DEFAULT_URL)
    try:
        run_client_repl(base_url=base_url)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
