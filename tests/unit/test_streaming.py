"""Тесты для agent/streaming.py — обработка событий стриминга."""
from unittest.mock import MagicMock
import json

import pytest

from agent.streaming import stream_interaction


class FakeEvent:
    """Простое событие с атрибутами."""
    def __init__(self, event_type, **kwargs):
        self.event_type = event_type
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestStreamErrorHandling:

    @pytest.mark.unit
    def test_error_event_raises_runtime_error(self):
        """event_type='error' должен бросить RuntimeError."""
        err = MagicMock()
        err.code = "rate_limit_exceeded"
        err.message = "Rate limit exceeded for model X"

        events = [FakeEvent("error", error=err)]

        client = MagicMock()
        client.interactions.create.return_value = iter(events)

        with pytest.raises(RuntimeError) as exc_info:
            stream_interaction(client, {"model": "test"})

        assert "rate_limit_exceeded" in str(exc_info.value)
        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.unit
    def test_error_event_without_error_object(self):
        """Если error=None — всё равно бросаем RuntimeError."""
        events = [FakeEvent("error", error=None)]
        client = MagicMock()
        client.interactions.create.return_value = iter(events)

        with pytest.raises(RuntimeError):
            stream_interaction(client, {"model": "test"})


class TestStreamFunctionCalls:

    @pytest.mark.unit
    def test_parses_function_call(self):
        """step.start + step.delta(arguments) → function_calls."""
        thought = MagicMock()
        thought.type = "thought"

        func_step = MagicMock()
        func_step.type = "function_call"
        func_step.name = "mt5_summary"
        func_step.id = "call_1"

        args_delta = MagicMock()
        args_delta.type = "arguments_delta"
        args_delta.arguments = '{"symbol":"XAUUSD"}'

        events = [
            FakeEvent("interaction.created", interaction=MagicMock(id="i_1")),
            FakeEvent("step.start", step=thought, index=0),
            FakeEvent("step.start", step=func_step, index=1),
            FakeEvent("step.delta", delta=args_delta, index=1),
            FakeEvent("interaction.completed"),
        ]

        client = MagicMock()
        client.interactions.create.return_value = iter(events)

        iid, text, calls = stream_interaction(client, {"model": "test"})

        assert iid == "i_1"
        assert text == ""
        assert len(calls) == 1
        assert calls[0]["name"] == "mt5_summary"
        assert calls[0]["arguments"] == {"symbol": "XAUUSD"}


class TestStreamText:

    @pytest.mark.unit
    def test_parses_text_delta(self):
        """step.delta(type='text') → text."""
        text_delta = MagicMock()
        text_delta.type = "text"
        text_delta.text = "Привет, мир"

        events = [
            FakeEvent("step.delta", delta=text_delta, index=0),
        ]

        client = MagicMock()
        client.interactions.create.return_value = iter(events)

        _, text, calls = stream_interaction(client, {"model": "test"})

        assert text == "Привет, мир"
        assert calls == []

    @pytest.mark.unit
    def test_empty_stream(self):
        """Пустой стрим → пустые значения."""
        client = MagicMock()
        client.interactions.create.return_value = iter([])

        iid, text, calls = stream_interaction(client, {"model": "test"})

        assert iid is None
        assert text == ""
        assert calls == []
