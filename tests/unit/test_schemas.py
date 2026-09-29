"""Тесты для agent/schemas.py — валидация Pydantic-моделей."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.schemas import (
    Plan,
    PlanStep,
    RiskApproval,
    ToolResult,
    ToolResultStatus,
    TradeSide,
    TradingSignal,
    to_json_schema,
)


# ============================================================
# ToolResult
# ============================================================

class TestToolResult:

    @pytest.mark.unit
    def test_ok_default(self):
        r = ToolResult(tool="mt5_summary")
        assert r.status == ToolResultStatus.OK
        assert r.text == ""
        assert r.data == {}
        assert r.error is None
        assert r.is_ok() is True
        assert r.is_error() is False

    @pytest.mark.unit
    def test_with_data(self):
        r = ToolResult(
            tool="mt5_summary",
            status=ToolResultStatus.OK,
            text="XAUUSD 2650",
            data={"price": 2650.5, "rsi": 45.2},
        )
        assert r.data["price"] == 2650.5
        assert r.data["rsi"] == 45.2
        assert r.is_ok() is True

    @pytest.mark.unit
    def test_error_status(self):
        r = ToolResult(
            tool="mt5_summary",
            status=ToolResultStatus.ERROR,
            error="MT5 not running",
        )
        assert r.is_ok() is False
        assert r.is_error() is True
        assert r.error == "MT5 not running"

    @pytest.mark.unit
    def test_blocked_status(self):
        r = ToolResult(
            tool="mt5_order",
            status=ToolResultStatus.BLOCKED,
            error="Live account blocked",
        )
        assert r.is_error() is True

    @pytest.mark.unit
    def test_empty_tool_name_fails(self):
        with pytest.raises(ValidationError):
            ToolResult(tool="")

    @pytest.mark.unit
    def test_negative_duration_fails(self):
        with pytest.raises(ValidationError):
            ToolResult(tool="test", duration_ms=-1)


# ============================================================
# TradingSignal
# ============================================================

class TestTradingSignal:

    @pytest.mark.unit
    def test_minimal(self):
        s = TradingSignal(symbol="XAUUSD", side=TradeSide.BUY)
        assert s.symbol == "XAUUSD"
        assert s.side == TradeSide.BUY
        assert s.confidence == 0.0
        assert s.entry is None
        assert s.timestamp.tzinfo is not None

    @pytest.mark.unit
    def test_full(self):
        s = TradingSignal(
            symbol="XAUUSD",
            side=TradeSide.SELL,
            entry=2650.0,
            sl=2660.0,
            tp=2620.0,
            confidence=0.75,
            reason="Bearish BOS on H1",
        )
        assert s.side == TradeSide.SELL
        assert s.entry == 2650.0
        assert s.sl == 2660.0
        assert s.tp == 2620.0
        assert s.confidence == 0.75
        assert "BOS" in s.reason

    @pytest.mark.unit
    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            TradingSignal(symbol="XAUUSD", side=TradeSide.BUY, confidence=1.5)
        with pytest.raises(ValidationError):
            TradingSignal(symbol="XAUUSD", side=TradeSide.BUY, confidence=-0.1)

    @pytest.mark.unit
    def test_negative_entry_fails(self):
        with pytest.raises(ValidationError):
            TradingSignal(symbol="XAUUSD", side=TradeSide.BUY, entry=-100.0)

    @pytest.mark.unit
    def test_invalid_side_fails(self):
        with pytest.raises(ValidationError):
            TradingSignal(symbol="XAUUSD", side="INVALID")

    @pytest.mark.unit
    def test_empty_symbol_fails(self):
        with pytest.raises(ValidationError):
            TradingSignal(symbol="", side=TradeSide.BUY)


# ============================================================
# RiskApproval
# ============================================================

class TestRiskApproval:

    @pytest.mark.unit
    def test_approved(self):
        r = RiskApproval(approved=True, max_lot=0.5, reason="Signal OK")
        assert r.approved is True
        assert r.max_lot == 0.5

    @pytest.mark.unit
    def test_rejected(self):
        r = RiskApproval(approved=False, reason="Too risky")
        assert r.approved is False
        assert r.max_lot == 0.0

    @pytest.mark.unit
    def test_negative_max_lot_fails(self):
        with pytest.raises(ValidationError):
            RiskApproval(approved=True, max_lot=-0.5)


# ============================================================
# Plan / PlanStep
# ============================================================

class TestPlan:

    @pytest.mark.unit
    def test_empty_plan(self):
        p = Plan(goal="Analyze XAUUSD")
        assert p.goal == "Analyze XAUUSD"
        assert p.steps == []
        assert p.created.tzinfo is not None

    @pytest.mark.unit
    def test_plan_with_steps(self):
        p = Plan(
            goal="Morning briefing",
            steps=[
                PlanStep(description="Get mt5_summary", tool="mt5_summary",
                         args={"symbol": "XAUUSD"}),
                PlanStep(description="Get econ_calendar",
                         tool="econ_calendar"),
                PlanStep(description="Send to Telegram",
                         tool="telegram_send"),
            ],
        )
        assert len(p.steps) == 3
        assert p.steps[0].tool == "mt5_summary"
        assert p.steps[0].args["symbol"] == "XAUUSD"
        assert p.steps[0].done is False

    @pytest.mark.unit
    def test_empty_goal_fails(self):
        with pytest.raises(ValidationError):
            Plan(goal="")

    @pytest.mark.unit
    def test_step_empty_description_fails(self):
        with pytest.raises(ValidationError):
            PlanStep(description="")


# ============================================================
# to_json_schema
# ============================================================

class TestJsonSchema:

    @pytest.mark.unit
    def test_tool_result_schema(self):
        schema = to_json_schema(ToolResult)
        assert schema["type"] == "object"
        assert "tool" in schema["properties"]
        assert "status" in schema["properties"]
        assert "data" in schema["properties"]

    @pytest.mark.unit
    def test_trading_signal_schema(self):
        schema = to_json_schema(TradingSignal)
        assert "symbol" in schema["properties"]
        assert "side" in schema["properties"]
        assert "confidence" in schema["properties"]

    @pytest.mark.unit
    def test_schema_has_required_fields(self):
        schema = to_json_schema(TradingSignal)
        # symbol и side — обязательные
        assert "symbol" in schema.get("required", [])
        assert "side" in schema.get("required", [])