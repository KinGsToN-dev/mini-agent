@echo off
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "start_tradingview.ps1"
pause