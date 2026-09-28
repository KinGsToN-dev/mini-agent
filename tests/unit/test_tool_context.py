"""Тесты для контекста инструментов (ContextVar в tools/registry.py)."""
import threading

import pytest

from tools.registry import (
    set_tool_context,
    get_tool_context,
    clear_tool_context,
    _tool_context,
)


class TestToolContext:

    @pytest.mark.unit
    def test_default_context_empty(self):
        clear_tool_context()
        ctx = get_tool_context()
        assert ctx == {} or ctx.get("chat_id") is None

    @pytest.mark.unit
    def test_set_chat_id(self):
        clear_tool_context()
        set_tool_context(chat_id=12345)
        ctx = get_tool_context()
        assert ctx["chat_id"] == 12345
        assert ctx["use_command_bot"] is False

    @pytest.mark.unit
    def test_set_use_command_bot(self):
        clear_tool_context()
        set_tool_context(chat_id=99, use_command_bot=True)
        ctx = get_tool_context()
        assert ctx["chat_id"] == 99
        assert ctx["use_command_bot"] is True

    @pytest.mark.unit
    def test_clear_context(self):
        set_tool_context(chat_id=1, use_command_bot=True)
        clear_tool_context()
        ctx = get_tool_context()
        assert ctx == {}

    @pytest.mark.unit
    def test_isolated_between_threads(self):
        """ContextVar изолирован между потоками."""
        results = {}

        def thread_a():
            set_tool_context(chat_id=111, use_command_bot=True)
            results["a"] = get_tool_context()

        def thread_b():
            set_tool_context(chat_id=222, use_command_bot=False)
            results["b"] = get_tool_context()

        t1 = threading.Thread(target=thread_a)
        t2 = threading.Thread(target=thread_b)
        t1.start(); t2.start()
        t1.join(); t2.join()

        assert results["a"]["chat_id"] == 111
        assert results["b"]["chat_id"] == 222

    @pytest.mark.unit
    def test_overwrite_context(self):
        """Повторная установка перезаписывает контекст."""
        set_tool_context(chat_id=1)
        set_tool_context(chat_id=2, use_command_bot=True)
        ctx = get_tool_context()
        assert ctx["chat_id"] == 2
        assert ctx["use_command_bot"] is True
