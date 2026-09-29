# Mini-Agent — State

**Дата:** 2026-09-29 10:57:52
**Ветка:** main
**Последний коммит:** 4249cca — Phase 2 + fix: smart provider routing (Mistral for code without tools, Gemini for code with tools)
**Тесты:** tests\unit\test_verifier.py .........................                    [100%] |  | ============================ 525 passed in 30.27s =============================
**Файлов .py:** 154
**Строк кода:** 21046

**Текущая фаза:** 2 — Pydantic-схемы (Verifier отложен до Фазы 7) (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

agent, agent_server, docs, providers, repl, repl_client, scripts, telegram_bot, tests, tools, _tv_dump, _tv_dump2, _tv_dump3, _verifier_backup

---

## Git status (на момент сохранения)

```
 M STATE.md M  providers/fallback.py  M tools/telegram_tools.py ?? agent.log.old
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