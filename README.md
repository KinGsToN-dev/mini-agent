Mini-Agent — AI-трейдинг агент для терминала
Мультипровайдерный AI-ассистент с 25 инструментами, торговлей MetaTrader 5,
автоматическими брифингами в Telegram и авто-переключением между моделями.

Работает бесплатно на Free Tier 4 провайдеров LLM.

✨ Что умеет
🧠 Мультипровайдер (4 источника)
Провайдер	Модели	Квота Free	Скорость
Gemini	lite-3.5, flash-3.5	1500/день, 20/день	3-20с
Groq	gpt-oss-20b, 120b, qwen	14 400/день	1-2с
Mistral	codestral	2000/день	2с
OpenRouter	9 free-моделей	50/день + fallback	2-18с
Авто-fallback: при 429/404 переключается на следующую модель.

🎯 Умные роутеры
Роутер провайдеров — трейдинг → Gemini, код → Mistral, общее → Groq

Роутер моделей — flash-3.5 для торговли, lite-3.5 для остального

Fallback в OpenRouter — если Gemini недоступен, идёт в OpenRouter

🛠 25 инструментов
Файлы и shell — run_shell, read_file, write_file, list_dir, grep

Система — processes, screenshot, screenshot_analyze, clipboard, notify, python_exec

Интернет — http_get, web_search

MT5 чтение — mt5_quote, mt5_bars, mt5_summary, mt5_account, mt5_positions

MT5 торговля — mt5_order, mt5_close, mt5_close_all, mt5_modify, mt5_pending

Новости — econ_calendar

Telegram — telegram_send

🔒 Безопасность
Whitelist безопасных команд (dir, type, python --version)

Blacklist запрещённых (format, mkfs, reg delete, rm -rf)

Опасные команды (del /s, rmdir /s) — подтверждение всегда

3 режима: ask / auto / dry

💾 Торговля с тройной защитой
Demo-first — live-аккаунт заблокирован по умолчанию

Лимит — не более 0.1 лота за раз

Callback подтверждения — панель YES/no перед операцией

Логирование — все ордера в trades.log

📅 Автоматизация
🌅 Утренний брифинг — 04:00 GMT+5

☀️ Дневной брифинг — 17:00 GMT+5

🌆 Вечерний брифинг — 18:30 GMT+5

💼 Мониторинг позиций — каждый час

Все брифинги приходят в Telegram.

🚀 Быстрый старт
powershell
cd C:\projects\mini-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
.\run.bat
🔑 Ключи API
Провайдер	Где получить	Free Tier
Gemini	https://aistudio.google.com/apikey	1500/день
Groq	https://console.groq.com/keys	14 400/день
Mistral	https://console.mistral.ai/api-keys	2000/день
OpenRouter	https://openrouter.ai/keys	50/день
Tavily	https://tavily.com	1000/мес
💬 Примеры
text
> сделай утренний брифинг по BTCUSD и отправь в телеграм
> купи 0.01 BTCUSD с SL 84000 и TP 86000
> закрой все позиции
> что на экране?
> найди в интернете свежие новости про BTC
> напиши функцию quicksort
📚 Документация
docs/PROVIDERS.md — провайдеры и модели

docs/TOOLS.md — 25 инструментов

docs/COMMANDS.md — команды REPL

docs/AUTOMATION.md — Task Scheduler

🧪 Тесты
powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/ -q
248 тестов на 3 версиях Python.

🎯 Принципы
Бесплатно — Free Tier 4 провайдеров

Безопасно — whitelist/blacklist + demo-first

Локально — сессии, логи на диске

Расширяемо — новый tool = 1 файл + регистрация

Мультипровайдер — авто-fallback между 4 источниками

📜 Лицензия
Личное использование.

