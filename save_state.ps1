# save_state.ps1
# Обновляет STATE.md + генерирует project_dump.txt
# Запуск: powershell -ExecutionPolicy Bypass -File .\save_state.ps1

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
Set-Location $Root

$StateFile = Join-Path $Root "STATE.md"
$DumpFile = Join-Path $Root "project_dump.txt"

Write-Host "=== 1/4: Собираем информацию ===" -ForegroundColor Cyan

$Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$LastCommit = "n/a"
$LastCommitMsg = "n/a"
try {
    $LastCommit = & git log -1 --format="%h" 2>&1
    $LastCommitMsg = & git log -1 --format="%s" 2>&1
} catch {}

$GitStatus = & git status --short 2>&1
if (-not $GitStatus) { $GitStatus = "(clean)" }

$Branch = & git rev-parse --abbrev-ref HEAD 2>&1

Write-Host "=== 2/4: Прогон тестов ===" -ForegroundColor Cyan
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) { $PythonExe = "python" }

$TestOutput = & $PythonExe -m pytest tests/unit/ -q 2>&1 | Select-Object -Last 3
$TestsLine = $TestOutput -join " | "

$PyFiles = Get-ChildItem -Path $Root -Recurse -Filter "*.py" -File | Where-Object {
    $_.FullName -notmatch "\\.venv\\" -and $_.FullName -notmatch "\\__pycache__\\"
}
$PyCount = $PyFiles.Count
$PyLines = ($PyFiles | ForEach-Object { (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines } | Measure-Object -Sum).Sum

Write-Host "  .py файлов: $PyCount, строк: $PyLines"

$TopDirs = Get-ChildItem -Path $Root -Directory | Where-Object {
    $_.Name -notmatch "^\.|^_backup|^__pycache__|^tv_screenshots|^sessions"
} | Select-Object -ExpandProperty Name

Write-Host "=== 3/4: Пишем STATE.md ===" -ForegroundColor Cyan

$StateContent = @"
# Mini-Agent — State

**Дата:** $Date
**Ветка:** $Branch
**Последний коммит:** $LastCommit — $LastCommitMsg
**Тесты:** $TestsLine
**Файлов .py:** $PyCount
**Строк кода:** $PyLines

---

## Roadmap: статус

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

## Что сделано (последние коммиты)

- fix: mt5_summary NameError (timezone) + duplicate screenshot in tv_analyze
- feat(phase1): add Verifier class + tests
- chore: ignore one-off patches and _verifier_backup/
- feat(core): force-send final text if Gemini forgot telegram_send; disable Verifier force-send
- fix(tradingview): send photo from tv_analyze (Gemini lite ignores instruction)
- fix(config): remove telegram_send_photo instruction (photo sent from tv_analyze)

---

## Что не сделано / в работе

### Verifier (Фаза 1)
- ✅ Класс Verifier (agent/verifier.py)
- ✅ 25 тестов (tests/unit/test_verifier.py)
- ⚠️ Отключён в agent/core.py — force-send ломает tool-call chain Gemini
- 📋 TODO: убрать _force_telegram_send из Verifier, оставить только retry

### Force-send (в core.py)
- ✅ Работает: если Gemini не вызвал telegram_send — текст уходит
- ⚠️ Не тестировалось в живом агенте (Gemini справлялся сам)

### Token Manager (Фаза 7)
- ⚠️ Fallback работает только внутри Gemini (MODEL_CATALOG)
- 📋 TODO: fallback на Groq/Mistral/OpenRouter при исчерпании Gemini

### Circular import
- ⚠️ telegram_tools: get_tool_context import failed — warning, не критично
- 📋 TODO: разорвать circular import в tools/registry.py

---

## Структура проекта (верхний уровень)

$($TopDirs -join ", ")

---

## Git status (на момент сохранения)

```
$GitStatus
```

---

## Как продолжить в новом чате

1. Скинь этот файл (STATE.md) + project_dump.txt.
2. Скажи: «Я на Фазе X, продолжаем».
3. Я прочитаю дамп и продолжу.

---

## Где смотреть логи

- agent.log — общий лог
- telegram_debug.log — telegram send/photo
- deps.log — MT5 / TradingView
- briefing.log — брифинги
- position_monitor.log — мониторинг позиций

---

## Известные баги

1. Verifier force-send — ломает tool-call chain Gemini (invalid_request).
2. Fallback только Gemini — при исчерпании всех Gemini-моделей не идёт в другие провайдеры.
3. Circular import — telegram_tools: get_tool_context import failed.
4. Dual BOM — при записи core.py через Python появляется двойной BOM.
"@

Set-Content -Path $StateFile -Value $StateContent -Encoding UTF8 -NoNewline
Write-Host "  [OK] STATE.md записан" -ForegroundColor Green

Write-Host "=== 4/4: Генерируем dump ===" -ForegroundColor Cyan
if (Test-Path (Join-Path $Root "dump_project.ps1")) {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $Root "dump_project.ps1") 2>&1 | Out-Null
    if (Test-Path $DumpFile) {
        $SizeKB = [math]::Round((Get-Item $DumpFile).Length / 1KB, 1)
        Write-Host "  [OK] project_dump.txt ($SizeKB KB)" -ForegroundColor Green
    }
} else {
    Write-Host "  [SKIP] dump_project.ps1 не найден" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== ГОТОВО ===" -ForegroundColor Green
Write-Host "STATE.md:          $StateFile" -ForegroundColor Cyan
Write-Host "project_dump.txt:  $DumpFile" -ForegroundColor Cyan
