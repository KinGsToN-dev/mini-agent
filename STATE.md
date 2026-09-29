# Mini-Agent — State

**Дата:** 2026-09-29 17:45:30
**Ветка:** main
**Последний коммит:** 9cbbbde — chore: simplify save_state.ps1 (keep manual sections), improve make_handoff.ps1
**Тесты:** tests\unit\test_verifier.py .........................                    [100%] |  | ============================ 525 passed in 32.41s =============================
**Файлов .py:** 156
**Строк кода:** 21485

**Текущая фаза:** 2 — Pydantic-схемы (Verifier отложен до Фазы 7) (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

agent, agent_server, docs, providers, repl, repl_client, scripts, telegram_bot, tests, tools, _tv_dump, _tv_dump2, _tv_dump3, _verifier_backup

---

## Git status (на момент сохранения)

```
M  STATE.md
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