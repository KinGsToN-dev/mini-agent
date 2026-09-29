"""Pydantic-схемы для mini-agent.

Типизированные структуры данных, которые используются между компонентами:
- ToolResult — структурированный результат вызова tool
- TradingSignal — торговый сигнал (от агента к пользователю)
- RiskApproval — решение риск-менеджера (одобрено/нет, лимит)
- Plan / PlanStep — план действий (задел для Фазы 11)

Почему это нужно:
- Явные контракты между модулями (не «строка на всё»)
- Валидация данных через Pydantic
- Возможность конвертировать в JSON Schema для LLM (structured output)
- Основа для Structured Handoff (Фаза 3), Tool Scoping (Фаза 4),
  Planning Agent (Фаза 11), Self-Review (Фаза 12)
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================
# Tool Result
# ============================================================

class ToolResultStatus(str, Enum):
    """Статус выполнения tool."""
    OK = "ok"
    ERROR = "error"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ToolResult(BaseModel):
    """Структурированный результат вызова tool.

    Attributes:
        tool: имя вызванного инструмента (например, "mt5_summary").
        status: OK / ERROR / BLOCKED / CANCELLED.
        text: текстовая часть результата — то, что видит пользователь.
        data: структурированные данные — то, что может использовать агент.
        error: текст ошибки, если status != OK.
        duration_ms: сколько миллисекунд занял вызов.
    """
    tool: str = Field(..., min_length=1, description="Имя tool")
    status: ToolResultStatus = ToolResultStatus.OK
    text: str = Field(default="", description="Текстовая часть (для человека)")
    data: dict[str, Any] = Field(default_factory=dict, description="Структурированные данные")
    error: Optional[str] = None
    duration_ms: int = Field(default=0, ge=0)

    def is_ok(self) -> bool:
        return self.status == ToolResultStatus.OK

    def is_error(self) -> bool:
        return self.status in (ToolResultStatus.ERROR, ToolResultStatus.BLOCKED)


# ============================================================
# Trading
# ============================================================

class TradeSide(str, Enum):
    """Направление сделки."""
    BUY = "BUY"
    SELL = "SELL"


class TradingSignal(BaseModel):
    """Торговый сигнал от агента.

    Attributes:
        symbol: торговый символ (XAUUSD, BTCUSD, ...).
        side: BUY или SELL.
        entry: цена входа (опционально).
        sl: Stop Loss (опционально).
        tp: Take Profit (опционально).
        confidence: уверенность 0.0 .. 1.0.
        reason: обоснование сигнала (текст от LLM).
        timestamp: когда создан сигнал (UTC).
    """
    symbol: str = Field(..., min_length=1, max_length=20)
    side: TradeSide
    entry: Optional[float] = Field(default=None, gt=0)
    sl: Optional[float] = Field(default=None, gt=0)
    tp: Optional[float] = Field(default=None, gt=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = Field(default="", max_length=2000)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskApproval(BaseModel):
    """Решение риск-менеджера по сигналу.

    Attributes:
        approved: одобрен ли сигнал к исполнению.
        max_lot: максимально допустимый объём (0 если не одобрено).
        reason: причина решения (текст).
    """
    approved: bool
    max_lot: float = Field(default=0.0, ge=0.0)
    reason: str = Field(default="", max_length=500)


# ============================================================
# Plan (задел для Фазы 11)
# ============================================================

class PlanStep(BaseModel):
    """Один шаг плана."""
    description: str = Field(..., min_length=1, max_length=500)
    tool: Optional[str] = Field(default=None, max_length=100)
    args: dict[str, Any] = Field(default_factory=dict)
    done: bool = False


class Plan(BaseModel):
    """План действий агента."""
    goal: str = Field(..., min_length=1, max_length=500)
    steps: list[PlanStep] = Field(default_factory=list)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Утилиты
# ============================================================

def to_json_schema(model_cls: type[BaseModel]) -> dict:
    """Конвертирует Pydantic-модель в JSON Schema.

    Используется для structured output в LLM (Gemini structured output).
    """
    return model_cls.model_json_schema()