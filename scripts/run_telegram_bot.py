"""Запуск Telegram-бота."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram_bot.bot import run_bot


def main():
    print("Telegram-бот mini-agent запускается...")
    print("Проверяю сервер...")
    try:
        from telegram_bot import config as cfg
        import httpx
        url = cfg.get_agent_server_url()
        r = httpx.get(f"{url}/health", timeout=5)
        if r.status_code != 200:
            print(f"[ERROR] Сервер {url} вернул {r.status_code}")
            sys.exit(1)
        print(f"[OK] Сервер {url} доступен")
    except Exception as e:
        print(f"[ERROR] Не могу подключиться: {e}")
        print("       Запусти: python scripts/run_agent_server.py")
        sys.exit(1)

    print("Ctrl+C для остановки")
    print()
    run_bot()


if __name__ == "__main__":
    main()
