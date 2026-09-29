# Mini-Agent — State

**Дата:** 2026-09-29 17:11:40
**Ветка:** main
**Последний коммит:** ccd0958 — fix(fallback): chain reset + router respects exhausted + gemini skips fallback (fixes invalid_request 500)
**Тесты:** tests\unit\test_verifier.py .........................                    [100%] |  | ============================ 525 passed in 31.47s =============================
**Файлов .py:** 159
**Строк кода:** 21598

**Текущая фаза:** 2 — Pydantic-схемы (Verifier отложен до Фазы 7) (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

agent, agent_server, docs, providers, repl, repl_client, scripts, telegram_bot, tests, tools, _tv_dump, _tv_dump2, _tv_dump3, _verifier_backup

---

## Git status (на момент сохранения)

```
M  ROADMAP.md M  STATE.md ?? _apply_chainfix.py ?? _apply_chainfix2.py ?? _apply_chainfix3.py ?? agent.log.old
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