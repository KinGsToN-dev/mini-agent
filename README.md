Порядок работы
Начнём с одного файла — README.md. Если сработает — сделаем остальные.

Шаг 1 — открой VS Code
File → Open Folder → C:\projects\mini-agent

Шаг 2 — удали старые файлы
В левой панели удали:

README.md (правой кнопкой → Delete)

commands.md

ARCHITECTURE.md

_make_docs.ps1

Шаг 3 — создай новый README
Правой кнопкой на папке MINI-AGENT → New File → имя README.md → Enter.

Шаг 4 — вставь текст
Скопируй ВЕСЬ текст ниже (начиная с # Mini-Agent и до последней строки):

Mini-Agent — мультипровайдерный AI-агент для терминала
Полноценный агент уровня Claude Desktop / Open Interpreter, работающий бесплатно на Free Tier трёх провайдеров LLM.

Возможности
Мультипровайдер
Gemini — vision, web_search, большая квота (1500/день на lite)

Groq — сверхбыстрый (0.5-1с), 14 400 запросов/день

Mistral — Codestral для кода (2000/день)

Переключение: /provider gemini|groq|mistral

Автоматический роутер
Сам выбирает провайдера под задачу

vision → Gemini, код → Mistral, web_search → Gemini+Tavily, остальное → Groq

Управление: /router on|off

13 инструментов
Инструмент	Назначение
run_shell	команды терминала (cmd)
read_file	чтение файлов
write_file	запись файлов
list_dir	структура папок
grep	поиск по файлам (regex)
processes	список/kill процессов
screenshot	скриншот экрана
screenshot_analyze	vision — описание экрана через Gemini
http_get	чтение веб-страниц
clipboard	буфер обмена
notify	Windows-уведомления
python_exec	Python-песочница
web_search	поиск в интернете через Tavily
Безопасность
Whitelist безопасных команд

Blacklist запрещённых (format, mkfs, reg delete)

Опасные команды (del /s, rm -rf) — подтверждение всегда

Защита от команд без слэша

3 режима: ask (по умолчанию) / auto / dry

Память и сессии
Локальное хранилище сообщений (JSONL)

/save, /load, /sessions, /delete, /rename, /history, /find

Экспорт в Markdown

Кэш исчерпанных моделей между запусками

UX
Стриминг ответов Gemini

Таймеры на каждом шаге

Красивые панели tool calls

Analytics: /stats

Установка
cd C:\projects\mini-agent

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

Copy-Item .env.example .env

Заполнить ключи в .env

.\run.bat

Где получить ключи
Провайдер	Где получить	Лимит Free Tier
Gemini	https://aistudio.google.com/apikey	1500/день (lite), 20/день (flash)
Groq	https://console.groq.com/keys	14 400/день
Mistral	https://console.mistral.ai/api-keys	2000/день (codestral)
Tavily	https://tavily.com	1000/мес
Быстрый старт
text
> привет                          → Groq, 0.66с
> напиши функцию quicksort        → Mistral, 1.14с, полный код
> что на экране?                  → Gemini, vision
> найди в интернете Python 3.13   → Gemini + Tavily
> что в папке?                    → Groq, tool-calling
Документация
commands.md — шпаргалка всех команд

ARCHITECTURE.md — как устроен проект

/help внутри агента

Принципы
Бесплатно — работает на Free Tier

Безопасно — whitelist + blacklist + подтверждения

Локально — сессии, история, логи на диске

Расширяемо — новый инструмент = 1 файл + регистрация

Мультипровайдер — 3 источника с fallback

Лицензия
Личное использование.