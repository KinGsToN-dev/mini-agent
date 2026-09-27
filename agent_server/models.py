"""Pydantic-модели для запросов/ответов API."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Запрос к /ask."""
    text: str = Field(..., min_length=1, max_length=10_000)
    session_id: str = Field(default="default", max_length=100)


class AskResponse(BaseModel):
    """Ответ от /ask."""
    answer: str
    provider: str = "gemini"
    model: str = "unknown"
    duration_ms: int = 0
    tool_calls: list = []


class StatusResponse(BaseModel):
    """Ответ от /status."""
    status: str = "ok"
    version: str
    provider: str
    model: str
    mode: str


class HealthResponse(BaseModel):
    """Ответ от /health."""
    status: str = "ok"
    version: str
