🔌 Провайдеры Mini-Agent
Агент поддерживает 4 провайдера LLM с автоматическим переключением
и fallback между ними.

📊 Сравнение провайдеров
Провайдер	Модели	Квота Free	Скорость	Tools	Vision
Gemini	lite-3.5, flash-3.5	1500/день, 20/день	3-20с	✅	✅
Groq	gpt-oss-20b, 120b, qwen, allam	14 400/день	1-2с	✅	❌
Mistral	codestral, large	2000/день	2с	❌	❌
OpenRouter	9 free-моделей	50/день + fallback	2-18с	✅	❌
🧠 Gemini (Google)
Где получить ключ
https://aistudio.google.com/apikey

Модели
Ключ	Имя	Квота	Особенность
lite-3.5	gemini-3.5-flash-lite	~1500/день	быстрая, для общих задач
flash-3.5	gemini-3.5-flash	~20/день	умная, для tool-chains
Возможности
✅ Vision — единственный провайдер, который видит картинки

✅ Web search — через Tavily

✅ Tool-calling — но lite не делает цепочек

✅ Стриминг ответов

✅ Грамотный русский

Особенности
lite-3.5 — быстрая, но не делает tool-chains. Если нужно 2-3 tool call подряд — используй flash-3.5

flash-3.5 — умная, но всего 20 запросов/день

Vision работает только через screenshot_analyze — отправляет PNG в Gemini

Когда использовать
Vision («что на экране?») — всегда

Торговля — flash-3.5 для tool-chains

Общие вопросы — lite-3.5 (быстро, экономит flash-квоту)

⚡ Groq
Где получить ключ
https://console.groq.com/keys

Модели
Ключ	Имя	Квота	Особенность
gpt-oss-20b	openai/gpt-oss-20b	14 400/день	быстрая, работает с tools
gpt-oss-120b	openai/gpt-oss-120b	1000/день	умная, но путает tools
qwen-27b	qwen/qwen3.8-27b	1000/день	средняя, лимит 7000 ITPM
allam	allam-2-7b	много	очень быстрая, 7B
Возможности
✅ Скорость — 1-2с (самый быстрый провайдер)

✅ Щедрая квота — 14 400 запросов/день

✅ Tool-calling — на gpt-oss-20b

❌ Vision — не умеет картинки

⚠️ Русский — иногда опечатки

Особенности
gpt-oss-20b — оптимальный выбор: быстрый + tools

gpt-oss-120b — мощный, но имеет встроенный Python tool, который конфликтует с нашими

qwen-27b — 7000 ITPM, не влезает контекст с 25 tools

Когда использовать
Общие вопросы («привет», «как дела»)

Быстрые задачи без vision

Брифинги — генерация текста через Groq

🌪 Mistral
Где получить ключ
https://console.mistral.ai/api-keys

Модели
Ключ	Имя	Квота	Особенность
codestral	codestral-latest	2000/день	заточен под код
large	mistral-large-latest	требует data-training	не работает на Free
small	mistral-small-latest	требует data-training	не работает на Free
nemo	open-mistral-nemo	может не работать	—
Возможности
✅ Код — Codestral заточен под программирование

✅ Грамотный русский

❌ Tool-calling — нет (свой формат API, не OpenAI)

❌ Vision — нет

Особенности
Codestral — работает, но без tools

Large/Small — требуют data-training (не работают на Free Tier)

Не поддерживает function calling — только диалог + генерация кода

Когда использовать
Генерация кода («напиши функцию quicksort»)

Рефакторинг («улучши этот код»)

Объяснение кода

Важно: для торговли не подходит — нет tool-calling.

🌐 OpenRouter
Где получить ключ
https://openrouter.ai/keys

Модели
Ключ	Имя	Особенность
llama-3.3-70b	meta-llama/llama-3.3-70b-instruct:free	топ free, отличный tool-calling
deepseek-r1	deepseek/deepseek-r1:free	reasoning, тоже с tools
qwen-72b	qwen/qwen-2.5-72b-instruct:free	средняя, с tools
qwen-coder	qwen/qwen3-coder:free	для кода
nemotron-120b	nvidia/nemotron-3-super-120b-a12b:free	умная, с tools
gpt-oss-120b	openai/gpt-oss-120b:free	OpenAI GPT-OSS
gpt-oss-20b	openai/gpt-oss-20b:free	быстрая
gemma-31b	google/gemma-4-31b-it:free	Google Gemma
free-router	openrouter/free	авто-выбор любой free модели
Возможности
✅ 9 free-моделей — можно переключаться

✅ Tool-calling — на большинстве

✅ Авто-fallback — при 429 переключается на следующую

✅ 50 запросов/день — общая квота

❌ Vision — нет (нужен Gemini)

Особенности
OpenRouter API — OpenAI-совместимый

Fallback работает автоматически — если Llama исчерпана, идёт в DeepSeek, потом Qwen, потом openrouter/free

Ограничение: массив моделей — не более 3 в одном запросе

openrouter/free — специальный эндпоинт, сам выбирает свободную free-модель

Когда использовать
Fallback для Gemini — если квота исчерпана

Альтернатива Groq — когда тот «капризничает»

Торговля — Llama 3.3 70B отлично делает tool-calls

🔀 Автоматический роутер провайдеров
Файл: agent/provider_router.py

Роутер сам выбирает провайдера под задачу:

Тип запроса	Приоритет	Fallback
Торговые действия («купи BTCUSD»)	Gemini	OpenRouter → Groq
Трейдинг («брифинг», «анализ»)	Gemini	OpenRouter → Groq
Web search («найди в интернете»)	Gemini	OpenRouter → Groq
Vision («что на экране»)	Gemini	—
Анализ («проанализируй код»)	Gemini	OpenRouter → Groq
Код («напиши функцию»)	Mistral	OpenRouter → Groq
Общее («привет»)	Groq	OpenRouter
Управление
text
> /router on     — включить авто-выбор
> /router off    — выключить (все запросы в текущего провайдера)
> /router        — показать статус
Когда отключать
При отладке — чтобы роутер не перебивал /provider

Когда квота Gemini исчерпана — вручную переключись на OpenRouter

🎯 Ручное переключение
text
> /provider gemini
> /provider groq
> /provider mistral
> /provider openrouter

> /model lite-3.5
> /model flash-3.5
> /model gpt-oss-20b
> /model llama-3.3-70b
> /model codestral

> /models        — список моделей текущего провайдера
💡 Стратегия использования
Для торговли
Основной: Gemini flash-3.5 (20/день)

Fallback: OpenRouter llama-3.3-70b (50/день)

Обход LLM: /call mt5_order {...} (без квоты)

Для брифингов
Основной: Groq gpt-oss-20b (14 400/день)

Не тратит Gemini квоту

Для кода
Основной: Mistral codestral (2000/день)

Для общих вопросов
Groq gpt-oss-20b — быстро, не тратит квоту

🔧 Как добавить нового провайдера
Если провайдер OpenAI-совместимый (Together, Cerebras, NIM и т.д.):

Создай providers/my_provider.py:

python
from providers.openai_compat import OpenAICompatProvider

MODELS = [
    ("model-key", "model-name", "описание"),
]

DEFAULT = "model-key"

def create(api_key: str):
    return OpenAICompatProvider(
        api_key=api_key,
        base_url="https://api.provider.com/v1",
        provider_name="my_provider",
        model_catalog=MODELS,
        default_model=DEFAULT,
    )
В providers/registry.py:

python
from providers import my_provider as my_mod

if name == "my_provider":
    api_key = os.getenv("MY_API_KEY")
    return my_mod.create(api_key)
В config.py:

python
PROVIDER_CATALOG["my_provider"] = MODELS
PROVIDER_DEFAULT_MODEL["my_provider"] = DEFAULT
В .env:

text
MY_API_KEY=...
Готово. Провайдер появится в /provider.

📌 Итог
4 провайдера, 18+ моделей, авто-fallback.

Gemini — vision + tool-chains

Groq — скорость

Mistral — код

OpenRouter — fallback + free-модели

Стратегия: используй каждого там, где он силён.