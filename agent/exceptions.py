"""Единая иерархия исключений mini-agent.

Все кастомные ошибки наследуются от AgentError.
Это позволяет:
  - ловить конкретно: except MT5Error: ...
  - различать типы ошибок в Verifier
  - понятные сообщения в логах
"""


class AgentError(Exception):
    """Base class for all agent errors."""
    pass


class MT5Error(AgentError):
    """MetaTrader 5 недоступен или операция не удалась.

    Примеры:
      - mt5.initialize() вернул False
      - символ не найден
      - ордер отклонён брокером
    """
    pass


class TradingViewError(AgentError):
    """TradingView CDP недоступен или график не удалось получить.

    Примеры:
      - CDP порт 9222 не отвечает
      - вкладка с tradingview.com/chart не найдена
      - скриншот слишком маленький
    """
    pass


class TelegramError(AgentError):
    """Ошибка Telegram API.

    Примеры:
      - токен не задан в .env
      - chat_id не найден
      - Telegram вернул 400/403/429
    """
    pass


class ProviderError(AgentError):
    """Ошибка LLM-провайдера (Gemini/Groq/Mistral/OpenRouter).

    Примеры:
      - rate limit exceeded (429)
      - модель не найдена (404)
      - API-ключ неверный (401)
    """
    pass


class ToolError(AgentError):
    """Инструмент не смог выполнить операцию.

    Примеры:
      - неизвестный tool name
      - неверные аргументы
      - внутренняя ошибка инструмента
    """
    pass


class ConfigError(AgentError):
    """Конфигурация или переменная окружения отсутствует.

    Примеры:
      - .env не найден
      - GEMINI_API_KEY не задан
      - MT5_PATH указывает на несуществующий файл
    """
    pass
