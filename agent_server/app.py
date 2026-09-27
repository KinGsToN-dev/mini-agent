"""FastAPI-приложение. Этап 1.1: скелет БЕЗ агента."""

from fastapi import FastAPI, HTTPException

from agent_server import __version__
from agent_server.config import API_VERSION
from agent_server.models import (
    AskRequest,
    AskResponse,
    HealthResponse,
    StatusResponse,
)

app = FastAPI(
    title="Mini-Agent HTTP API",
    version=API_VERSION,
    description="REST API для mini-agent. Этап 1.1 — скелет.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Проверка, что сервер жив."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """Текущий статус агента. Заглушка до Этапа 1.2."""
    return StatusResponse(
        status="ok",
        version=__version__,
        provider="gemini",
        model="not-connected-yet",
        mode="ask",
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """
    Основной эндпоинт — задать вопрос агенту.
    Этап 1.1: заглушка. Этап 1.2: подключим реальный GeminiAgent.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Пустой текст запроса")

    # Заглушка
    return AskResponse(
        answer=f"[NOT IMPLEMENTED] Получено: {req.text!r} (session={req.session_id})",
        provider="stub",
        model="stub",
        duration_ms=0,
        tool_calls=[],
    )


@app.get("/")
def root():
    """Корневой эндпоинт — для быстрой проверки в браузере."""
    return {
        "name": "Mini-Agent HTTP API",
        "version": __version__,
        "docs": "/docs",
        "endpoints": ["/health", "/status", "/ask"],
    }
