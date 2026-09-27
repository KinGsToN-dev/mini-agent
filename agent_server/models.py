"""Pydantic-модели для запросов/ответов API."""

from typing import Optional

from pydantic import BaseModel, Field


# --- /ask ---

class AskRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    session_id: str = Field(default="default", max_length=100)


class AskResponse(BaseModel):
    answer: str
    provider: str = "unknown"
    model: str = "unknown"
    duration_ms: int = 0
    tool_calls: list = []
    session_id: str = "default"


# --- /status ---

class StatusResponse(BaseModel):
    status: str = "ok"
    version: str
    provider: str
    model: str
    mode: str
    router_enabled: bool = True
    auto_route: bool = True
    sessions: int = 0


# --- /health ---

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


# --- /reset ---

class ResetRequest(BaseModel):
    session_id: str = Field(default="default", max_length=100)


class ResetResponse(BaseModel):
    status: str
    session_id: str
    existed: bool


# --- /forget ---

class ForgetResponse(BaseModel):
    status: str
    cleared_sessions: int


# --- /providers ---

class ProviderInfo(BaseModel):
    name: str
    available: bool
    is_current: bool


class ProvidersResponse(BaseModel):
    current: str
    providers: list


# --- /provider ---

class SwitchProviderRequest(BaseModel):
    provider: str = Field(..., min_length=2, max_length=50)
    session_id: str = Field(default="default", max_length=100)


# --- /model ---

class SwitchModelRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(default="default", max_length=100)


class SwitchResponse(BaseModel):
    status: str
    session_id: str
    provider: Optional[str] = None
    model: Optional[str] = None
