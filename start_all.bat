@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   Запуск mini-agent (сервер + Telegram-бот)
echo ==================================================
echo.

echo [1/2] Запускаю сервер mini-agent (отдельное окно)...
start "mini-agent server" cmd /k ".venv\Scripts\python.exe scripts\run_agent_server.py"

echo [..] Жду, пока сервер будет готов...

:wait_loop
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_loop

echo [OK] Сервер отвечает на /health.
echo.
echo [2/2] Запускаю Telegram-бота (отдельное окно)...
start "mini-agent telegram-bot" cmd /k ".venv\Scripts\python.exe scripts\run_telegram_bot.py"

echo.
echo ==================================================
echo   ГОТОВО
echo ==================================================
echo.
echo Открыты 2 окна:
echo   1. "mini-agent server"        - HTTP-сервер агента
echo   2. "mini-agent telegram-bot"  - Telegram-бот
echo.
echo Оба можно свернуть. Комп НЕ выключай.
echo.
echo Для остановки:
echo   - закрой оба окна
echo   - или Ctrl+C в каждом
echo.
pause