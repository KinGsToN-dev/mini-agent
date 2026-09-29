# Mini-Agent — State

**Дата:** 2026-09-29 10:18:04
**Ветка:** main
**Последний коммит:** 5fed493 — Phase 2: add Pydantic schemas (ToolResult, TradingSignal, RiskApproval, Plan) + 22 tests
**Тесты:** tests\unit\test_verifier.py .........................                    [100%] |  | ============================ 525 passed in 30.44s =============================
**Файлов .py:** 150
**Строк кода:** 19987

**Текущая фаза:** 2 — Pydantic-схемы (Verifier отложен до Фазы 7) (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

agent, agent_server, docs, providers, repl, repl_client, scripts, telegram_bot, tests, tools, _tv_dump, _tv_dump2, _tv_dump3, _verifier_backup

---

## Git status (на момент сохранения)

```
M  agent/core.py A  providers/capabilities.py A  tests/unit/test_capabilities.py
```

---

## Как продолжить в новом чате

1. Скинь этот файл (STATE.md) + ROADMAP.md + project_dump.txt.
2. Скажи: «Я на Фазе X, продолжаем».
3. Я прочитаю и продолжу.

---

## Логи

- agent.log — общий лог
- telegram_debug.log — telegram send/photo
- deps.log — MT5 / TradingView
- briefing.log — брифинги
- position_monitor.log — мониторинг позиций