🛠 Инструменты Mini-Agent
Агент имеет 25 инструментов, которые вызываются автоматически через
function calling. LLM сама решает, какой инструмент использовать.

📁 Файлы и shell
run_shell
Назначение: выполнить команду в терминале Windows (cmd).

Параметры:

command (str) — команда

Пример:

text
> покажи что в папке
[run_shell {'command': 'dir'}]
Безопасность:

Whitelist безопасных (dir, type, echo, python --version)

Blacklist запрещённых (format, mkfs, reg delete, rm -rf)

Серая зона → подтверждение

read_file
Назначение: прочитать файл.

Параметры:

path (str) — путь

Пример:

text
> прочитай config.py
[read_file {'path': 'config.py'}]
write_file
Назначение: записать текст в файл (создать/перезаписать).

Параметры:

path (str) — путь

content (str) — содержимое

Пример:

text
> создай hello.py с print("hi")
[write_file {'path': 'hello.py', 'content': 'print("hi")'}]
list_dir
Назначение: структурированный список файлов и папок.

Параметры:

path (str, опц.) — путь (по умолчанию .)

recursive (bool, опц.) — рекурсивно

pattern (str, опц.) — фильтр (*.py)

Пример:

text
> покажи все .py файлы рекурсивно
[list_dir {'pattern': '*.py', 'recursive': True}]
grep
Назначение: поиск текста (regex) в файлах.

Параметры:

pattern (str) — regex

path (str, опц.) — где искать

file_pattern (str, опц.) — фильтр файлов

max_results (int, опц.) — лимит

Пример:

text
> найди все TODO
[grep {'pattern': 'TODO'}]
💻 Система
processes
Назначение: список/kill процессов Windows.

Параметры:

action (str) — list или kill

filter (str, опц.) — фильтр по имени

sort_by (str, опц.) — cpu / memory / name

top (int, опц.) — сколько показать

pid (int, опц.) — для kill

name (str, опц.) — для kill

Пример:

text
> что грузит CPU?
[processes {'action': 'list', 'sort_by': 'cpu', 'top': 10}]

> убей Chrome
[processes {'action': 'kill', 'name': 'chrome'}]
screenshot
Назначение: скриншот экрана в PNG (без анализа).

Параметры:

save_path (str, опц.) — куда сохранить

Пример:

text
> сделай скриншот
[screenshot {'save_path': 'screenshot.png'}]
screenshot_analyze ⭐
Назначение: скриншот + описание через Gemini vision.

Параметры:

prompt (str, опц.) — что спросить

save_path (str, опц.) — куда сохранить

Пример:

text
> что на экране?
[screenshot_analyze {'prompt': 'Опиши что на экране'}]

> прочитай ошибку на экране
[screenshot_analyze {'prompt': 'Найди текст ошибки'}]
Важно: работает только через Gemini (только он умеет картинки).

clipboard
Назначение: буфер обмена (только текст).

Параметры:

action (str) — get или set

text (str, опц.) — что записать

Пример:

text
> скопируй в буфер: привет мир
[clipboard {'action': 'set', 'text': 'привет мир'}]

> что в буфере?
[clipboard {'action': 'get'}]
notify
Назначение: Windows-уведомление (toast).

Параметры:

title (str, опц.) — заголовок

message (str) — текст

duration (int, опц.) — секунды

Пример:

text
> уведоми меня что задача завершена
[notify {'title': 'Готово', 'message': 'Задача завершена'}]
python_exec
Назначение: выполнить Python-код в песочнице.

Параметры:

code (str) — код

timeout (int, опц.) — секунды

cwd (str, опц.) — рабочая директория

Пример:

text
> посчитай 2 в 100
[python_exec {'code': 'print(2**100)'}]
Запрещено: os, subprocess, shutil, eval, exec, open.

🌐 Интернет
http_get
Назначение: GET-запрос по URL.

Параметры:

url (str) — адрес

timeout (int, опц.) — секунды

save_to (str, опц.) — сохранить в файл

Пример:

text
> прочитай https://example.com
[http_get {'url': 'https://example.com'}]
Запрещено: localhost, 127.*, 192.168.*, 10.*.

web_search
Назначение: поиск в интернете через Tavily.

Параметры:

query (str) — запрос

max_results (int, опц.) — лимит

Пример:

text
> найди в интернете свежие новости про BTC
[web_search {'query': 'BTC news', 'max_results': 5}]
Требует: TAVILY_API_KEY в .env.

📊 MT5 — чтение
mt5_quote
Назначение: текущая котировка (bid/ask).

Параметры:

symbol (str) — символ (BTCUSD, XAUUSD, EURUSD)

Пример:

text
> покажи котировку BTCUSD
[mt5_quote {'symbol': 'BTCUSD'}]
mt5_bars
Назначение: OHLC-свечи.

Параметры:

symbol (str)

timeframe (str, опц.) — M1, M5, M15, M30, H1, H4, D1, W1, MN1

count (int, опц.) — сколько свечей

Пример:

text
> покажи свечи BTCUSD H1 за 24 часа
[mt5_bars {'symbol': 'BTCUSD', 'timeframe': 'H1', 'count': 24}]
mt5_summary
Назначение: сводка по символу — цена, изменение 24ч, диапазон, MA20, MA50, RSI, тренд.

Параметры:

symbol (str)

Пример:

text
> сделай сводку по BTCUSD
[mt5_summary {'symbol': 'BTCUSD'}]
Идеально для брифингов.

mt5_account
Назначение: информация об аккаунте.

Параметры: нет

Пример:

text
> покажи баланс
[mt5_account {}]
mt5_positions
Назначение: открытые позиции.

Параметры: нет

Пример:

text
> покажи мои позиции
[mt5_positions {}]
💰 MT5 — торговля
Все торговые операции требуют подтверждения (панель YES/no) и работают
только на demo по умолчанию.

mt5_order
Назначение: открыть рыночный ордер.

Параметры:

symbol (str)

side (str) — BUY или SELL

volume (float) — объём (не более MAX_LOT, по умолчанию 0.1)

sl (float, опц.) — Stop Loss

tp (float, опц.) — Take Profit

comment (str, опц.)

Пример:

text
> купи 0.01 BTCUSD с SL 84000 и TP 86000
[mt5_order {'symbol': 'BTCUSD', 'side': 'BUY', 'volume': 0.01, 'sl': 84000, 'tp': 86000}]

🚨 ПОДТВЕРЖДЕНИЕ ТОРГОВОЙ ОПЕРАЦИИ 🚨
BTCUSD BUY 0.01
  Цена: 84486.3
  SL: 84000
  TP: 86000
  Аккаунт: 239920 (DEMO)
Подтвердить? (YES/no): YES
[OK] Ордер размещён. Ticket: 156280911
mt5_close
Назначение: закрыть позицию по ticket.

Параметры:

ticket (int)

Пример:

text
> закрой позицию 156280911
[mt5_close {'ticket': 156280911}]
mt5_close_all
Назначение: закрыть все позиции.

Параметры: нет

Пример:

text
> закрой все позиции
[mt5_close_all {}]

🚨 ЗАКРЫТЬ ВСЕ ПОЗИЦИИ
  Количество: 4
  Общая прибыль: -3.85
Подтвердить? (YES/no): YES
[OK] Закрыто 4 из 4
mt5_modify
Назначение: изменить SL/TP существующей позиции.

Параметры:

ticket (int)

sl (float, опц.)

tp (float, опц.)

Пример:

text
> поставь SL 83000 для позиции 156280911
[mt5_modify {'ticket': 156280911, 'sl': 83000}]
mt5_pending
Назначение: отложенный ордер.

Параметры:

symbol (str)

side (str) — BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP

price (float)

volume (float)

sl, tp (опц.)

Пример:

text
> поставь BUY_LIMIT 0.01 BTCUSD по 82000
[mt5_pending {'symbol': 'BTCUSD', 'side': 'BUY_LIMIT', 'price': 82000, 'volume': 0.01}]
📰 Новости
econ_calendar
Назначение: экономический календарь через Biquote.

Параметры:

countries (str, опц.) — US,EU,GB,JP

importance (str, опц.) — low, medium, high, all

limit (int, опц.) — сколько показать

only_upcoming (bool, опц.) — только будущие

Пример:

text
> что важного в США сегодня?
[econ_calendar {'countries': 'US', 'importance': 'high', 'limit': 10}]

🔴 2026-09-29 14:00 UTC  USD  CB Consumer Confidence Index
   прогноз: 89.4 | пред: 89.4
📱 Telegram
telegram_send
Назначение: отправить сообщение в Telegram.

Параметры:

message (str) — текст

title (str, опц.) — заголовок (жирный)

Пример:

text
> отправь в телеграм: анализ BTC завершён, цена 84500
[telegram_send {'message': 'Анализ BTC завершён...', 'title': 'BTC Update'}]
Требует: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID в .env.

🎯 Ручной вызов — /call
Любой инструмент можно вызвать напрямую, обходя LLM:

text
> /call mt5_quote {"symbol": "BTCUSD"}
> /call mt5_order {"symbol": "BTCUSD", "side": "BUY", "volume": 0.01}
> /call mt5_close_all {}
> /call telegram_send {"message": "тест"}
> /call
Когда использовать:

LLM не вызывает инструмент (галлюцинирует)

Квота Gemini исчерпана

Хочешь точный контроль

/call работает всегда — не зависит от LLM.

🔒 Алиасы инструментов
Модель иногда путает имена. Для этого есть TOOL_ALIASES в tools/registry.py:

Что может написать	Куда попадёт
send_telegram_message	telegram_send
search_web	web_search
buy / sell	mt5_order
close_position	mt5_close
get_quote	mt5_quote
calendar	econ_calendar
Если модель ошиблась — алиас сам перенаправит.

💡 Примеры комплексных сценариев
Сценарий 1: брифинг + отправка
text
> сделай утренний брифинг по BTCUSD и отправь в телеграм
[mt5_summary {'symbol': 'BTCUSD'}]
[econ_calendar {'importance': 'high'}]
[telegram_send {'message': '...', 'title': '🌅 Утренний брифинг'}]
Сценарий 2: торговля
text
> купи 0.01 BTCUSD с SL 84000 и TP 86000
[mt5_quote {'symbol': 'BTCUSD'}]
[mt5_order {'symbol': 'BTCUSD', 'side': 'BUY', 'volume': 0.01, 'sl': 84000, 'tp': 86000}]
Сценарий 3: анализ экрана
text
> что на экране?
[screenshot_analyze {'prompt': 'Опиши что на экране'}]
Сценарий 4: поиск + сводка
text
> найди в интернете новости про BTC и сделай сводку
[web_search {'query': 'BTC news today'}]
[mt5_summary {'symbol': 'BTCUSD'}]
📊 Итого
Категория	Инструментов
Файлы и shell	5
Система	6
Интернет	2
MT5 чтение	5
MT5 торговля	5
Новости	1
Telegram	1
ВСЕГО	25
