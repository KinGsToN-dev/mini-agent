# Mini-Agent — State

**Дата:** 2026-09-29 08:41:34
**Ветка:** main
**Последний коммит:** 2f00ed7 — fix(config): remove telegram_send_photo instruction (photo sent from tv_analyze)
**Тесты:** tests\unit\test_verifier.py .........................                    [100%] |  | ============================ 455 passed in 30.41s =============================
**Файлов .py:** 141
**Строк кода:** 18441

**Текущая фаза:** 2 — Pydantic-схемы (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

agent, agent_server, docs, providers, repl, repl_client, scripts, telegram_bot, tests, tools, _tv_dump, _tv_dump2, _tv_dump3, _verifier_backup

---

## Git status (на момент сохранения)

```
M  .gitignore A  ROADMAP.md A  STATE.md A  make_handoff.ps1 A  save_state.ps1 A  save_state_no_dump.ps1
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