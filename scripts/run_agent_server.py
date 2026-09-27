"""Запуск HTTP-сервера mini-agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

from agent_server.config import HOST, PORT


def main():
    print(f"Agent Server запущен на http://{HOST}:{PORT}")
    print(f"Документация: http://{HOST}:{PORT}/docs")
    print(f"Проверка:     http://{HOST}:{PORT}/health")
    print()
    print("Для остановки: Ctrl+C")
    print()

    uvicorn.run(
        "agent_server.app:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
