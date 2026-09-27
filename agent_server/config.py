"""Конфигурация HTTP-сервера."""

import os

# Хост и порт (только localhost — безопасно)
HOST = os.getenv("AGENT_SERVER_HOST", "127.0.0.1")
PORT = int(os.getenv("AGENT_SERVER_PORT", "8765"))

# Версия API
API_VERSION = "0.1.0"

# Максимальная длина текста запроса
MAX_TEXT_LENGTH = 10_000
