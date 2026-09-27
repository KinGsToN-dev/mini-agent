📅 Автоматизация Mini-Agent
Агент умеет работать без тебя через Windows Task Scheduler:
брифинги приходят в Telegram автоматически, мониторинг позиций следит за P&L.

🎯 Что автоматизируется
Задача	Время (GMT+5)	Что делает
🌅 Morning Briefing	04:00	Утренний брифинг (перед азиатской сессией)
☀️ Midday Briefing	17:00	Дневной брифинг (за 30 мин до NY-новостей)
🌆 Evening Briefing	18:30	Вечерний брифинг (после NY-новостей)
💼 Position Monitor	Каждый час	Отчёт по позициям (если есть)
Все брифинги приходят в Telegram.

📂 Структура скриптов
text
scripts/
├── daily_briefing.py     — брифинг (3 режима через --mode)
├── position_monitor.py   — мониторинг позиций
└── task_manager.py       — управление задачами
📝 daily_briefing.py
Один скрипт — 3 режима.

Режимы
Режим	Что показывает
--mode daily	Утренний: обзор рынка, что будет сегодня, сценарии
--mode midday	Дневной: рынок сейчас, что через 30-60 мин, план действий
--mode evening	Вечерний: реакция на новости, что вышло, план на азию
Как работает
Сбор данных (~2с):

mt5_summary для BTCUSD, XAUUSD, EURUSD

econ_calendar — события дня

Анализ через Groq (~10с):

Отправляет данные в gpt-oss-20b

Промпт под режим → получает красивый текст

Отправка в Telegram (~1с)

Итого: ~13 секунд.

Запуск вручную
powershell
# Утренний
.\.venv\Scripts\python.exe scripts\daily_briefing.py --mode daily

# Дневной
.\.venv\Scripts\python.exe scripts\daily_briefing.py --mode midday

# Вечерний
.\.venv\Scripts\python.exe scripts\daily_briefing.py --mode evening
Логи
Все запуски пишутся в briefing.log:

text
[2026-09-27 17:00:01] [midday] БРИФИНГ [midday] — старт
[2026-09-27 17:00:03] [midday] [1/3] Сбор данных...
[2026-09-27 17:00:04] [midday]       OK (2.1с, 2100 символов)
[2026-09-27 17:00:14] [midday] [2/3] Анализ через Groq...
[2026-09-27 17:00:14] [midday]       OK (9.0с, 2685 символов)
[2026-09-27 17:00:15] [midday] [3/3] Отправка в Telegram...
[2026-09-27 17:00:15] [midday]       [OK] Отправлено (2707 символов)
[2026-09-27 17:00:15] [midday] ГОТОВО (общее время: 14.2с)
💼 position_monitor.py
Что делает:

Запускается каждый час

Проверяет mt5_positions

Если позиций нет → молчит

Если P&L не изменился → молчит (не спамит)

Если P&L изменился → отправляет отчёт в Telegram

Отчёт
text
💼 МОНИТОРИНГ ПОЗИЦИЙ
2026-09-27 17:40 UTC (22:40 GMT+5)

📊 Открытых позиций: 1

🔴 BTCUSD BUY 0.01
   Открытие: 84486.31
   Текущая:  84428.44
   P&L:      -0.58

━━━━━━━━━━━━━━━━━━━━━━━━

💰 АККАУНТ:
   Баланс: $200 000.00
   Equity: $199 999.42
   Маржа: $424.86
   Свободная маржа: $199 574.56
   Прибыль: -0.58

📈 Общая прибыль: -0.58
Логика «не спамить»
Состояние сохраняется в positions_state.json:

json
{
  "total_profit": -0.58,
  "count": 1,
  "updated": "2026-09-27T17:40:00+00:00"
}
При следующем запуске:

P&L -0.58 → -0.58 = не изменился → молчим

P&L -0.58 → -1.20 = изменился → отправляем

Запуск вручную
powershell
.\.venv\Scripts\python.exe scripts\position_monitor.py
🔧 task_manager.py
Единая точка управления всеми задачами.

Команды
Команда	Что делает
list	Список всех задач из реестра
create --task-name X --time HH:MM	Создать задачу
create --task-name X --interval hourly	Создать почасовую задачу
delete --task-name X	Удалить
enable --task-name X	Включить (если была отключена)
disable --task-name X	Отключить
status --task-name X	Показать статус
run-now --task-name X	Запустить немедленно
change-time HH:MM --task-name X	Изменить время
Доступные задачи (реестр)
Ключ	Имя	Скрипт	Режим
briefing	Mini-Agent Morning Briefing	daily_briefing.py --mode daily	04:00 ежедневно
midday	Mini-Agent Midday Briefing	daily_briefing.py --mode midday	17:00 ежедневно
evening	Mini-Agent Evening Briefing	daily_briefing.py --mode evening	18:30 ежедневно
monitor	Mini-Agent Position Monitor	position_monitor.py	каждый час
🚀 Установка (первый раз)
1. Создать все задачи
powershell
cd C:\projects\mini-agent

# Утренний
.\.venv\Scripts\python.exe scripts\task_manager.py create --task-name briefing --time 04:00

# Дневной
.\.venv\Scripts\python.exe scripts\task_manager.py create --task-name midday --time 17:00

# Вечерний
.\.venv\Scripts\python.exe scripts\task_manager.py create --task-name evening --time 18:30

# Мониторинг
.\.venv\Scripts\python.exe scripts\task_manager.py create --task-name monitor --interval hourly
2. Проверить
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py list
Ожидаемо:

text
  briefing: Mini-Agent Morning Briefing       Статус: создана
  midday:   Mini-Agent Midday Briefing        Статус: создана
  evening:  Mini-Agent Evening Briefing       Статус: создана
  monitor:  Mini-Agent Position Monitor       Статус: создана
🎯 Управление задачами
Отключить на время (отпуск)
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py disable --task-name briefing
.\.venv\Scripts\python.exe scripts\task_manager.py disable --task-name midday
.\.venv\Scripts\python.exe scripts\task_manager.py disable --task-name evening
.\.venv\Scripts\python.exe scripts\task_manager.py disable --task-name monitor
Включить обратно
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py enable --task-name briefing
Изменить время
powershell
# Вечерний на 19:00
.\.venv\Scripts\python.exe scripts\task_manager.py change-time 19:00 --task-name evening
Запустить немедленно (тест)
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py run-now --task-name briefing
Удалить полностью
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py delete --task-name midday
🔍 Проверка через Task Scheduler GUI
Win+R → taskschd.msc → Enter

Найди задачу → правой кнопкой → Свойства:

Триггеры — время запуска

Действия — путь к Python + скрипт

Условия — Wake computer, батареи

Журнал — история запусков, код возврата

Код возврата:

0x0 — успех

Другое — ошибка (смотри логи)

📋 Регистрация новых задач
Если хочешь добавить новую задачу:

1. Создай скрипт в scripts/
2. Добавь в task_manager.py в TASKS:
python
"my_task": {
    "name": "Mini-Agent My Task",
    "script": "my_script.py",
    "script_args": ["--arg1", "value"],
    "default_time": "12:00",
    "default_interval": "daily",
    "description": "Моя новая задача",
},
3. Создай задачу
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py create --task-name my_task --time 12:00
⚙️ Настройки Windows
Wake computer
Чтобы задача будила компьютер из сна:

taskschd.msc → найди задачу → Свойства

Условия → ✅ Пробуждать компьютер для выполнения задачи

Скрипт уже добавляет это автоматически.

Батареи
Если ноутбук на батарее — задача может не запуститься.

Фикс: в task_manager.py уже добавлены:

xml
<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
Питание
Чтобы компьютер не засыпал насовсем:

Параметры → Система → Питание

Спящий режим → Никогда (или подходящее время)

Wake computer сработает только если компьютер в S3 (Sleep), не в S5 (Hibernate).

🧪 Тестовые запуски
Тест 1 — запустить каждую задачу немедленно
powershell
.\.venv\Scripts\python.exe scripts\task_manager.py run-now --task-name briefing
.\.venv\Scripts\python.exe scripts\task_manager.py run-now --task-name midday
.\.venv\Scripts\python.exe scripts\task_manager.py run-now --task-name evening
В Telegram придёт 3 разных брифинга.

Тест 2 — проверить в GUI
taskschd.msc

Найди задачу

Журнал → Task Started / Action Completed

Код возврата: 0x0

Тест 3 — проверить логи
powershell
Get-Content briefing.log | Select-Object -Last 20
Get-Content position_monitor.log | Select-Object -Last 20
🐛 Возможные проблемы
Задача создана, но не запускается
Причина: schtasks требует прав администратора для некоторых задач.

Фикс: запусти PowerShell от имени администратора, потом создай задачу.

Wake computer не работает
Причина: Windows не будит из Hibernate (S4).

Фикс:

Параметры → Питание → Никогда не переводить в спящий режим

Или перевести в Sleep (S3) вместо Hibernate (S4)

Брифинг не приходит в Telegram
Проверка:

briefing.log — что было

.env — TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

Ручной запуск — python scripts/daily_briefing.py --mode daily

Position Monitor молчит
Это нормально — если позиций нет или P&L не изменился.

Проверка:

powershell
type positions_state.json
Изменения в task_manager.py не применились
Причина: старые задачи в Task Scheduler не обновляются автоматически.

Фикс: пересоздай задачу:

powershell
.\.venv\Scripts\python.exe scripts\task_manager.py delete --task-name evening
.\.venv\Scripts\python.exe scripts\task_manager.py create --task-name evening --time 18:30
📊 Расписание (полный день)
Время GMT+5	UTC	Задача
04:00	23:00	🌅 Утренний брифинг
05:00 – 16:59	—	Мониторинг позиций (каждый час)
17:00	12:00	☀️ Дневной брифинг
18:30	13:30	🌆 Вечерний брифинг
19:00 – 03:59	—	Мониторинг позиций (каждый час)
Итого: 3 брифинга + ~24 проверки позиций в день.

💡 Стратегия использования
Для активного трейдинга
Включи все 4 задачи

Читай брифинги, следи за позициями

Для пассивного наблюдения
Только Morning + Evening

disable для midday и monitor

Для отпуска
disable все 4 задачи

enable когда вернёшься

Для отладки
run-now для немедленного запуска

Смотри логи в *.log

🎯 Итог
4 задачи покрывают полный торговый день:

3 брифинга (утро, день, вечер)

Мониторинг (каждый час)

Управление — через task_manager.py (create, delete, enable, disable, change-time).

Проверка — через taskschd.msc и логи.

Всё автоматически — ты просыпаешься, а Telegram уже полон отчётов.