@echo off
cd /d "%~dp0"

start "mini-agent server" cmd /k ".venv\Scripts\python.exe scripts\run_agent_server.py"
timeout /t 3 /nobreak >nul

start "mini-agent telegram-bot" cmd /k ".venv\Scripts\python.exe scripts\run_telegram_bot.py"
timeout /t 2 /nobreak >nul

echo Запускаю REPL-клиент...
.venv\Scripts\python.exe main_client.py