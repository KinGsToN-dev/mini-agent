@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   Запуск mini-agent
echo ==================================================
echo.

echo [1/2] Запускаю сервер...
start "mini-agent server" cmd /k "chcp 65001 >nul && .venv\Scripts\python.exe scripts\run_agent_server.py"

echo [..] Жду, пока сервер будет готов...

:wait_loop
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_loop

echo [OK] Сервер готов.
echo.
echo [2/2] Запускаю Telegram-бота...
start "mini-agent telegram-bot" cmd /k "chcp 65001 >nul && .venv\Scripts\python.exe scripts\run_telegram_bot.py"

echo.
echo ==================================================
echo   ГОТОВО
echo ==================================================
echo.
echo 2 окна открыты:
echo   1. mini-agent server
echo   2. mini-agent telegram-bot
echo.
echo Теперь открой Telegram и напиши боту #2:
echo   проанализируй XAUUSD с моими индикаторами
echo.
pause