# Mini-Agent — State

**Дата:** 2026-09-29 09:42:38
**Ветка:** main
**Последний коммит:** 40db6eb — chore: add ROADMAP.md + STATE.md + handoff scripts + auto-update hook
**Тесты:** tests\unit\test_verifier.py .........................                    [100%] |  | ============================ 477 passed in 33.13s =============================
**Файлов .py:** 144
**Строк кода:** 18747

**Текущая фаза:** 2 — Pydantic-схемы (Verifier отложен до Фазы 7) (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

agent, agent_server, docs, providers, repl, repl_client, scripts, telegram_bot, tests, tools, _tv_dump, _tv_dump2, _tv_dump3, _verifier_backup

---

## Git status (на момент сохранения)

```
M  ROADMAP.md M  STATE.md M  agent/__init__.py A  agent/schemas.py A  tests/unit/test_schemas.py
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