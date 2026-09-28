# Mini-Agent — AI-трейдинг агент для терминала

Мультипровайдерный AI-ассистент с 28 инструментами, торговлей MetaTrader 5,
анализом графиков TradingView через Gemini Vision,
автоматическими брифингами в Telegram и авто-переключением между моделями.

Работает бесплатно на Free Tier 4 провайдеров LLM.

---

## ✨ Что умеет

### 🧠 Мультипровайдер (4 источника)

| Провайдер | Модели | Квота Free | Скорость | Tools | Vision |
|-----------|--------|-----------|----------|-------|--------|
| **Gemini** | lite-3.5, flash-3.5 | 1500/день, 20/день | 3-20с | ✅ | ✅ |
| **Groq** | gpt-oss-20b, 120b, qwen | 14 400/день | 1-2с | ⚠️ только простые | ❌ |
| **Mistral** | codestral | 2000/день | 2с | ❌ | ❌ |
| **OpenRouter** | 9 free-моделей | 50/день + fallback | 2-18с | ✅ | ❌ |

Авто-fallback: при 429/404 переключается на следующую модель.

### 🎯 Умные роутеры

- **Роутер провайдеров** — трейдинг → **Gemini** (важно: не Groq, там ломается tool-calling), код → Mistral, общее → Groq, vision → Gemini.
- **Роутер моделей** — flash-3.5 для торговли, lite-3.5 для остального.
- **Fallback в OpenRouter** — если Gemini недоступен, идёт в OpenRouter.

### 🛠 28 инструментов

- **Файлы и shell** — run_shell, read_file, write_file, list_dir, grep
- **Система** — processes, screenshot, screenshot_analyze, clipboard, notify, python_exec
- **Интернет** — http_get, web_search
- **MT5 чтение** — mt5_quote, mt5_bars, mt5_summary, mt5_account, mt5_positions
- **MT5 торговля** — mt5_order, mt5_close, mt5_close_all, mt5_modify, mt5_pending
- **Новости** — econ_calendar
- **TradingView** — tv_screenshot, tv_analyze (Gemini Vision читает индикаторы с графика)
- **Telegram** — telegram_send, telegram_send_photo

### 🔒 Безопасность

- Whitelist безопасных команд (dir, type, python --version)
- Blacklist запрещённых (format, mkfs, reg delete, rm -rf)
- Опасные команды (del /s, rmdir /s) — подтверждение всегда
- 3 режима: ask / auto / dry

### 💾 Торговля с тройной защитой

- Demo-first — live-аккаунт заблокирован по умолчанию
- Лимит — не более 0.1 лота за раз
- Callback подтверждения — панель YES/no перед операцией
- Логирование — все ордера в trades.log

### 📅 Автоматизация

- 🌅 Утренний брифинг — 04:00 GMT+5
- ☀️ Дневной брифинг — 17:00 GMT+5
- 🌆 Вечерний брифинг — 18:30 GMT+5
- 💼 Мониторинг позиций — каждый час

Все брифинги приходят в Telegram **от командного бота** (bot #2), в тот же чат,
откуда был отправлен запрос.

### 🤖 Multi-agent (reflexion)

Агент не только выполняет задачу, но и **проверяет результат**:

1. **Force-send**: если Gemini забыл вызвать `telegram_send` после анализа —
   сервер принудительно отправляет финальный текст в Telegram.
2. **Explicit context**: `tv_analyze` явно передаёт `chat_id` и `use_command_bot`
   в `telegram_send_photo` (не полагается на `ContextVar`, который теряется
   после `asyncio.run`).
3. **Token priority**: `telegram_tools` всегда использует `TELEGRAM_COMMAND_BOT_TOKEN`,
   если он есть в `.env` — независимо от контекста.

---

## 🚀 Быстрый старт

```powershell
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
Telegram Bot #1 (RSIbot)	@BotFather	TELEGRAM_BOT_TOKEN
Telegram Bot #2 (Command)	@BotFather	TELEGRAM_COMMAND_BOT_TOKEN
💬 Примеры
text
> проанализируй XAUUSD с скриншотом
> сделай утренний брифинг по BTCUSD и отправь в телеграм
> купи 0.01 BTCUSD с SL 84000 и TP 86000
> закрой все позиции
> что на экране?
> найди в интернете свежие новости про BTC
> напиши функцию quicksort
📚 Документация
docs/PROVIDERS.md — провайдеры и модели

docs/TOOLS.md — 28 инструментов

docs/COMMANDS.md — команды REPL

docs/AUTOMATION.md — Task Scheduler

🧪 Тесты
powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/ -q
395 тестов на 3 версиях Python (3.10, 3.11, 3.12) через GitHub Actions.

🎯 Принципы
Бесплатно — Free Tier 4 провайдеров

Безопасно — whitelist/blacklist + demo-first

Локально — сессии, логи на диске

Расширяемо — новый tool = 1 файл + регистрация

Мультипровайдер — авто-fallback между 4 источниками

Multi-agent — reflexion: агент проверяет свою работу

📜 Лицензия
Личное использование.
