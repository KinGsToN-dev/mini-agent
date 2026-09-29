# Mini-Agent — Roadmap

**Текущая фаза:** 2 — Pydantic-схемы

---

## Статус фаз

| Фаза | Что | Статус |
|------|-----|--------|
| 0 | База (оркестрация, tools, router) | ✅ Готово |
| 1 | Verifier | ⚠️ Отключён (force-send ломает tool-call chain) |
| 2 | Pydantic-схемы | ⏳ Следующая |
| 3 | Structured Handoff | ❌ Не начато |
| 4 | Tool Scoping | ❌ Не начато |
| 5 | Pipeline Engine | ❌ Не начато |
| 6 | Human-in-the-Loop | ❌ Не начато |
| 7 | Token Manager | ❌ Не начато |
| 8 | Memory Agent (краткосрочная) | ❌ Не начато |
| 9 | Long-Term Memory | ❌ Не начато |
| 10 | Episodic Memory | ❌ Не начато |
| 11 | Planning Agent | ❌ Не начато |
| 12 | Self-Review Agent | ❌ Не начато |
| 13 | Proactive Agent | ❌ Не начато |
| 14 | Voice | ❌ Не начато |
| 15 | Multi-User | ❌ Не начато |
| 16 | Plugin System | ❌ Не начато |
| 17 | Web UI | ❌ Не начато |

---

## Фаза 1: Verifier — детали

- ✅ Класс `Verifier` (`agent/verifier.py`)
- ✅ 25 тестов (`tests/unit/test_verifier.py`)
- ⚠️ **Отключён** в `agent/core.py` — force-send ломает tool-call chain Gemini
- 📋 TODO: убрать `_force_telegram_send` из `Verifier`, оставить только retry

## Фаза 2: Pydantic-схемы — план

- Создать `agent/schemas.py` с моделями:
  - `TradingSignal` — symbol, side, entry, sl, tp, confidence, reason
  - `RiskApproval` — approved, max_lot, reason
  - `ToolResult` — структурированный результат tool-call
- Обновить tools, чтобы они возвращали JSON, а не строки

---

## Известные баги

1. **Verifier force-send** — ломает tool-call chain Gemini (`invalid_request`).
2. **Fallback только Gemini** — при исчерпании всех Gemini-моделей не идёт в другие провайдеры.
3. **Circular import** — `telegram_tools: get_tool_context import failed`.
4. **Dual BOM** — при записи `core.py` через Python появляется двойной BOM.