# save_state_no_dump.ps1 — быстрая версия без дампа
# Обновляет STATE.md (дата, коммит, тесты, файлы, git status).
# Roadmap НЕ трогает — он в ROADMAP.md.
# Запуск: powershell -ExecutionPolicy Bypass -File .\save_state_no_dump.ps1

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
Set-Location $Root

$StateFile = Join-Path $Root "STATE.md"
$RoadmapFile = Join-Path $Root "ROADMAP.md"

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

$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) { $PythonExe = "python" }

$TestOutput = & $PythonExe -m pytest tests/unit/ -q 2>&1 | Select-Object -Last 3
$TestsLine = $TestOutput -join " | "

$PyFiles = Get-ChildItem -Path $Root -Recurse -Filter "*.py" -File | Where-Object {
    $_.FullName -notmatch "\\.venv\\" -and $_.FullName -notmatch "\\__pycache__\\"
}
$PyCount = $PyFiles.Count
$PyLines = ($PyFiles | ForEach-Object { (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines } | Measure-Object -Sum).Sum

# Текущая фаза из ROADMAP.md
$CurrentPhase = "?"
if (Test-Path $RoadmapFile) {
    $rm = Get-Content $RoadmapFile -Raw -Encoding UTF8
    if ($rm -match "\*\*Текущая фаза:\*\*\s*([^\r\n]+)") {
        $CurrentPhase = $matches[1].Trim()
    }
}

$TopDirs = Get-ChildItem -Path $Root -Directory | Where-Object {
    $_.Name -notmatch "^\.|^_backup|^__pycache__|^tv_screenshots|^sessions"
} | Select-Object -ExpandProperty Name

# Тройные бэктики через переменную — нельзя писать ``` в here-string
$bt = [char]96 + [char]96 + [char]96

$StateContent = @"
# Mini-Agent — State

**Дата:** $Date
**Ветка:** $Branch
**Последний коммит:** $LastCommit — $LastCommitMsg
**Тесты:** $TestsLine
**Файлов .py:** $PyCount
**Строк кода:** $PyLines

**Текущая фаза:** $CurrentPhase (см. ROADMAP.md)

---

## Структура проекта (верхний уровень)

$($TopDirs -join ", ")

---

## Git status (на момент сохранения)

$bt
$GitStatus
$bt

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
"@

Set-Content -Path $StateFile -Value $StateContent -Encoding UTF8 -NoNewline
Write-Host "  [OK] STATE.md updated" -ForegroundColor Green