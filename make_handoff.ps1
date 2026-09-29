# make_handoff.ps1
# Готовит STATE.md + project_dump.txt для смены чата
# Запуск: powershell -ExecutionPolicy Bypass -File .\make_handoff.ps1

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
Set-Location $Root

Write-Host "=== Готовим handoff ===" -ForegroundColor Cyan

if (Test-Path ".\save_state.ps1") {
    & powershell -ExecutionPolicy Bypass -File ".\save_state.ps1"
} else {
    Write-Host "[ERROR] save_state.ps1 не найден" -ForegroundColor Red
    exit 1
}

if (Test-Path ".\dump_project.ps1") {
    Write-Host ""
    Write-Host "=== Генерируем project_dump.txt ===" -ForegroundColor Cyan
    & powershell -ExecutionPolicy Bypass -File ".\dump_project.ps1" 2>&1 | Out-Null
}

$StateFile = Join-Path $Root "STATE.md"
$DumpFile = Join-Path $Root "project_dump.txt"

Write-Host ""
Write-Host "=== Handoff готов ===" -ForegroundColor Green
Write-Host ""
Write-Host "Файлы для скидывания в новый чат:" -ForegroundColor Yellow
if (Test-Path $StateFile) {
    $size = [math]::Round((Get-Item $StateFile).Length / 1KB, 1)
    Write-Host "  1. STATE.md ($size KB)" -ForegroundColor White
}
if (Test-Path $DumpFile) {
    $size = [math]::Round((Get-Item $DumpFile).Length / 1KB, 1)
    Write-Host "  2. project_dump.txt ($size KB)" -ForegroundColor White
}
if (Test-Path (Join-Path $Root "ROADMAP.md")) {
    $size = [math]::Round((Get-Item (Join-Path $Root "ROADMAP.md")).Length / 1KB, 1)
    Write-Host "  3. ROADMAP.md ($size KB) - правится вручную" -ForegroundColor White
}

Write-Host ""
Write-Host "Что написать в новом чате:" -ForegroundColor Yellow
Write-Host "  Продолжаем с Фазы X. Вот STATE.md + ROADMAP.md + project_dump.txt." -ForegroundColor White