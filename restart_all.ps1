# ============================================================
# restart_all.ps1
# Restart mini-agent: kill old server+bot windows by title, start new ones.
# Pure ASCII - works with PowerShell 5.1.
# ============================================================

chcp 65001 >$null
$ErrorActionPreference = "Continue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Restart mini-agent (server + Telegram bot)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. Kill old cmd windows by MainWindowTitle ---
Write-Host "[1/6] Killing old cmd windows (mini-agent server/bot)..." -ForegroundColor Cyan
$killedWindows = 0
$cmdProcs = Get-Process -Name "cmd" -ErrorAction SilentlyContinue
foreach ($p in $cmdProcs) {
    try {
        $title = $p.MainWindowTitle
        if ($title -and ($title -match "mini-agent server" -or $title -match "mini-agent telegram-bot")) {
            Write-Host ("  Killing PID " + $p.Id + " : " + $title) -ForegroundColor Yellow
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            $killedWindows++
        }
    } catch {
        # ignore
    }
}
if ($killedWindows -eq 0) {
    Write-Host "  No old cmd windows found" -ForegroundColor Green
} else {
    Write-Host ("  Killed windows: " + $killedWindows) -ForegroundColor Green
}
Start-Sleep -Milliseconds 500

# --- 2. Kill old python processes ---
Write-Host ""
Write-Host "[2/6] Killing old python processes (mini-agent)..." -ForegroundColor Cyan
$killed = 0
$pyProcs = Get-Process -Name "python", "pythonw" -ErrorAction SilentlyContinue
foreach ($p in $pyProcs) {
    try {
        $path = $p.Path
        if ($path -and ($path -like "*mini-agent*" -or $path -like "*\.venv\*")) {
            Write-Host ("  Killing PID " + $p.Id + " (" + $p.ProcessName + ")") -ForegroundColor Yellow
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            $killed++
        }
    } catch {
        # no access to Path - skip
    }
}
if ($killed -eq 0) {
    Write-Host "  No old python processes found" -ForegroundColor Green
} else {
    Write-Host ("  Killed python: " + $killed) -ForegroundColor Green
}

# --- 3. Check port 8765 ---
Write-Host ""
Write-Host "[3/6] Checking port 8765..." -ForegroundColor Cyan
$portBusy = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($portBusy) {
    $ownerPid = $portBusy.OwningProcess
    Write-Host ("  Port 8765 busy (PID " + $ownerPid + "). Killing...") -ForegroundColor Yellow
    Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}
$portBusy = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($portBusy) {
    Write-Host "  [WARN] Port still busy - waiting 2 sec" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
} else {
    Write-Host "  Port 8765 is free" -ForegroundColor Green
}

# --- 4. Start server in separate window ---
Write-Host ""
Write-Host "[4/6] Starting server (separate window)..." -ForegroundColor Cyan
$serverArgs = '/k title mini-agent server & chcp 65001 >nul & .venv\Scripts\python.exe scripts\run_agent_server.py'
Start-Process cmd -ArgumentList $serverArgs -WorkingDirectory "C:\projects\mini-agent" -WindowStyle Minimized
Write-Host "  [OK] Server started" -ForegroundColor Green

# --- 5. Wait for server to be ready ---
Write-Host ""
Write-Host "[5/6] Waiting for server to be ready..." -ForegroundColor Cyan
$maxWait = 30
$waited = 0
$serverReady = $false
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $serverReady = $true
            break
        }
    } catch {
        # not ready yet
    }
    if ($waited % 5 -eq 0) {
        Write-Host ("  ... " + $waited + " sec") -ForegroundColor DarkGray
    }
}
if (-not $serverReady) {
    Write-Host ""
    Write-Host ("[ERROR] Server did not respond on /health in " + $maxWait + " sec") -ForegroundColor Red
    Write-Host "        Check server window for startup errors" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ("  [OK] Server ready in " + $waited + " sec") -ForegroundColor Green

# --- 6. Start bot in separate window ---
Write-Host ""
Write-Host "[6/6] Starting Telegram bot (separate window)..." -ForegroundColor Cyan
$botArgs = '/k title mini-agent telegram-bot & chcp 65001 >nul & .venv\Scripts\python.exe scripts\run_telegram_bot.py'
Start-Process cmd -ArgumentList $botArgs -WorkingDirectory "C:\projects\mini-agent" -WindowStyle Minimized
Write-Host "  [OK] Bot started" -ForegroundColor Green
Start-Sleep -Seconds 2

# --- Summary ---
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  DONE" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "2 windows opened (minimized - restore for logs):" -ForegroundColor Cyan
Write-Host "  1. mini-agent server" -ForegroundColor White
Write-Host "  2. mini-agent telegram-bot" -ForegroundColor White
Write-Host ""
Write-Host "Now open Telegram - bot #2 (My MiniAgent Command Bot)." -ForegroundColor Cyan
Write-Host "Send:" -ForegroundColor Cyan
Write-Host "  proanaliziruy XAUUSD s skrinshotom" -ForegroundColor Yellow
Write-Host ""
Write-Host "Both message and screenshot must arrive in the SAME chat (bot #2)." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
