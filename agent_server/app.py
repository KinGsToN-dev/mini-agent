"""FastAPI-приложение. Этап 1.2: подключён GeminiAgent."""

import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from agent_server import __version__
from agent_server.config import API_VERSION
from agent_server.models import (
    AskRequest,
    AskResponse,
    ForgetResponse,
    HealthResponse,
    ProviderInfo,
    ProvidersResponse,
    ResetRequest,
    ResetResponse,
    StatusResponse,
    SwitchModelRequest,
    SwitchProviderRequest,
    SwitchResponse,
)
from agent_server.session_manager import (
    DEFAULT_SESSION_ID,
    SessionManager,
)

load_dotenv()

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Startup / shutdown HTTP-сервера."""
    # Startup: проверяем ключ и создаём SessionManager
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY не найден в .env — сервер не может стартовать"
        )
    _get_session_manager()
    yield
    # Shutdown: ничего делать не нужно

app = FastAPI(
    title="Mini-Agent HTTP API",
    version=API_VERSION,
    description="REST API для mini-agent. Этап 1.2 — реальный агент.",
    lifespan=lifespan,
)

# --- SessionManager создаётся при старте ---
_session_manager: SessionManager | None = None


def _get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY не найден в .env",
            )
        _session_manager = SessionManager(api_key=api_key)
    return _session_manager


# ============================================================
# /health
# ============================================================

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


# ============================================================
# /status
# ============================================================

@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    sm = _get_session_manager()
    agent = sm.get_or_create(DEFAULT_SESSION_ID)

    # Режим shell
    try:
        from tools.shell import get_mode
        mode = get_mode()
    except Exception:
        mode = "ask"

    return StatusResponse(
        status="ok",
        version=__version__,
        provider=agent.provider_name,
        model=agent.model_name,
        mode=mode,
        router_enabled=getattr(agent, "router_enabled", True),
        auto_route=getattr(agent, "auto_route", True),
        sessions=sm.count(),
    )


# ============================================================
# /ask
# ============================================================

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Пустой текст запроса")

    sm = _get_session_manager()
    try:
        agent = sm.get_or_create(req.session_id)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))

    t0 = time.time()
    try:
        answer = agent.ask(req.text)
    except Exception as e:
        # Обрезаем длинные ошибки
        err_text = str(e)
        if len(err_text) > 500:
            err_text = err_text[:500] + "...[обрезано]"
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {err_text}",
        )
    dt = int((time.time() - t0) * 1000)

    return AskResponse(
        answer=answer or "(пустой ответ)",
        provider=agent.provider_name,
        model=agent.model_name,
        duration_ms=dt,
        tool_calls=[],
        session_id=req.session_id or DEFAULT_SESSION_ID,
    )


# ============================================================
# /reset
# ============================================================

@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest) -> ResetResponse:
    sm = _get_session_manager()
    existed = sm.reset(req.session_id or DEFAULT_SESSION_ID)
    return ResetResponse(
        status="ok",
        session_id=req.session_id or DEFAULT_SESSION_ID,
        existed=existed,
    )


# ============================================================
# /forget — сброс кэша исчерпанных моделей
# ============================================================

@app.post("/forget", response_model=ForgetResponse)
def forget() -> ForgetResponse:
    sm = _get_session_manager()
    count = 0
    for sid in sm.list_sessions():
        try:
            agent = sm.get_or_create(sid)
            agent.exhausted.clear()
            try:
                from agent.state import clear_state
                clear_state()
            except Exception:
                pass
            count += 1
        except Exception:
            pass
    return ForgetResponse(status="ok", cleared_sessions=count)


# ============================================================
# /providers
# ============================================================

@app.get("/providers", response_model=ProvidersResponse)
def providers() -> ProvidersResponse:
    try:
        from providers import registry as provider_registry
        available = provider_registry.available_providers()
    except Exception:
        available = []

    sm = _get_session_manager()
    agent = sm.get_or_create(DEFAULT_SESSION_ID)

    result = []
    for p in ["gemini", "groq", "mistral", "openrouter"]:
        result.append(ProviderInfo(
            name=p,
            available=(p in available),
            is_current=(p == agent.provider_name),
        ))

    return ProvidersResponse(current=agent.provider_name, providers=result)


# ============================================================
# /provider — переключить провайдера
# ============================================================

@app.post("/provider", response_model=SwitchResponse)
def switch_provider(req: SwitchProviderRequest) -> SwitchResponse:
    sm = _get_session_manager()
    agent = sm.get_or_create(req.session_id or DEFAULT_SESSION_ID)

    try:
        name, model = agent.switch_provider(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    return SwitchResponse(
        status="ok",
        session_id=req.session_id or DEFAULT_SESSION_ID,
        provider=name,
        model=model,
    )


# ============================================================
# /model — переключить модель
# ============================================================

@app.post("/model", response_model=SwitchResponse)
def switch_model(req: SwitchModelRequest) -> SwitchResponse:
    sm = _get_session_manager()
    agent = sm.get_or_create(req.session_id or DEFAULT_SESSION_ID)

    try:
        new_name = agent.switch_model(req.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    return SwitchResponse(
        status="ok",
        session_id=req.session_id or DEFAULT_SESSION_ID,
        provider=agent.provider_name,
        model=new_name,
    )


# ============================================================
# Корень
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Mini-Agent HTTP API",
        "version": __version__,
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/status",
            "/ask",
            "/reset",
            "/forget",
            "/providers",
            "/provider",
            "/model",
        ],
    }
