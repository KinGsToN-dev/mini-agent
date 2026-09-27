"""Утренний / дневной / вечерний брифинг.

Режимы:
    daily    — утренний (04:00 GMT+5): перед азиатской сессией
    midday   — дневной (17:00 GMT+5): за 30 мин до NY-новостей
    evening  — вечерний (18:30 GMT+5): сразу после NY-новостей

Запуск: python scripts/daily_briefing.py [--mode daily|midday|evening]
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from tools.mt5_tools import mt5_summary
from tools.news_tools import econ_calendar
from tools.telegram_tools import telegram_send


# ============================================================
# Настройки
# ============================================================
SYMBOLS = ["BTCUSD", "XAUUSD", "EURUSD"]
COUNTRIES = "US,EU,GB"
IMPORTANCE = "high"

PROJECT_DIR = Path(__file__).parent.parent
LOG_FILE = PROJECT_DIR / "briefing.log"


# Режимы: название + промпт для LLM
MODES = {
    "daily": {
        "title": "🌅 Утренний брифинг",
        "prompt": (
            "Ты — опытный финансовый аналитик. Напиши УТРЕННИЙ брифинг "
            "(перед азиатской сессией).\n\n"
            "ДАННЫЕ:\n{data}\n\n"
            "ФОРМАТ (для Telegram, БЕЗ таблиц Markdown):\n\n"
            "🌅 УТРЕННИЙ БРИФИНГ\n"
            "[дата, время UTC / GMT+5]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 ОБЗОР РЫНКА\n"
            "**BTCUSD** — $[цена], тренд [восходящий/нисходящий/боковой]\n"
            "**XAUUSD** — $[цена], ...\n"
            "**EURUSD** — $[цена], ...\n\n"
            "📰 ЧТО БУДЕТ СЕГОДНЯ\n"
            "[события с временем UTC и GMT+5, прогнозы]\n"
            "ВАЖНО: различай СЕГОДНЯ и ЗАВТРА. Если событие завтра — пиши 'ЗАВТРА в HH:MM'.\n"
            "Если сегодня важных событий нет — честно напиши 'На сегодня важных событий нет'.\n"
            "НЕ ВЫДУМЫВАЙ события, которых нет в данных!\n\n"
            "🎯 СЦЕНАРИИ НА ДЕНЬ\n"
            "[бычий/медвежий для каждого символа]\n\n"
            "💡 ВЫВОДЫ\n"
            "[краткие выводы по каждому символу]\n\n"
            "⚠️ Это не торговые сигналы. Риск-менеджмент обязателен.\n\n"
            "ВАЖНО: НЕ используй Markdown-таблицы, НЕ используй HTML <br>,\n"
            "максимум 3500 символов, пиши грамотно на русском."
        ),
    },
    "midday": {
        "title": "☀️ Дневной брифинг",
        "prompt": (
            "Ты — опытный финансовый аналитик. Напиши ДНЕВНОЙ брифинг "
            "(за 30 минут до открытия NY-сессии и выхода американских новостей).\n\n"
            "ДАННЫЕ:\n{data}\n\n"
            "ФОРМАТ (для Telegram, БЕЗ таблиц):\n\n"
            "☀️ ДНЕВНОЙ БРИФИНГ\n"
            "[дата, время UTC / GMT+5]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 РЫНОК СЕЙЧАС\n"
            "**BTCUSD** — $[цена], [тренд]\n"
            "**XAUUSD** — $[цена], ...\n"
            "**EURUSD** — $[цена], ...\n\n"
            "⏰ ВНИМАНИЕ: ЧЕРЕЗ 30-60 МИН\n"
            "[список новостей, которые выйдут в ближайший час —\n"
            "прогнозы, важность, ожидаемое влияние]\n"
            "ВАЖНО: если в ближайший час событий нет — напиши\n"
            "'В ближайший час важных событий не ожидается'.\n"
            "НЕ ВЫДУМЫВАЙ события! Используй ТОЛЬКО данные из календаря.\n\n"
            "🎯 ПЛАН ДЕЙСТВИЙ\n"
            "[как подготовиться к волатильности:\n"
            "- закрыть/защитить существующие позиции\n"
            "- где ставить стопы\n"
            "- куда смотреть при пробое уровней]\n\n"
            "💡 ВЫВОДЫ\n\n"
            "⚠️ Это не торговые сигналы.\n\n"
            "ВАЖНО: НЕ используй Markdown-таблицы, НЕ используй <br>,\n"
            "максимум 3500 символов."
        ),
    },
    "evening": {
        "title": "🌆 Вечерний брифинг",
        "prompt": (
            "Ты — опытный финансовый аналитик. Напиши ВЕЧЕРНИЙ брифинг "
            "(сразу после выхода NY-новостей — CPI/JOLTS/NFP/FED).\n\n"
            "ДАННЫЕ:\n{data}\n\n"
            "ФОРМАТ (для Telegram, БЕЗ таблиц):\n\n"
            "🌆 ВЕЧЕРНИЙ БРИФИНГ\n"
            "[дата, время UTC / GMT+5]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 РЕАКЦИЯ РЫНКА\n"
            "**BTCUSD** — $[цена], [изменение за последний час]\n"
            "**XAUUSD** — $[цена], ...\n"
            "**EURUSD** — $[цена], ...\n\n"
            "📰 ЧТО ВЫШЛО (факт vs прогноз)\n"
            "[каждое событие:\n"
            "- название\n"
            "- время UTC/GMT+5\n"
            "- ФАКТ vs ПРОГНОЗ (если есть в данных)\n"
            "- реакция рынка]\n"
            "КРИТИЧНО ВАЖНО: используй ТОЛЬКО события из данных.\n"
            "Если в данных НЕТ событий с actual (фактом) — напиши\n"
            "'Сегодня важных событий не выходило'.\n"
            "НЕ ВЫДУМЫВАЙ CPI, NFP, FED или другие события!\n"
            "Если не уверен — лучше не пиши вообще.\n\n"
            "📈 РЕАКЦИЯ РЫНКА\n"
            "[как отреагировали BTC/XAU/EUR — вверх/вниз, насколько]\n\n"
            "📅 ЧТО БУДЕТ НА АЗИАТСКОЙ СЕССИИ\n"
            "[события на ближайшие часы: BoJ, China PMI и т.д.]\n\n"
            "🎯 СЦЕНАРИИ НА ВЕЧЕР\n"
            "[бычий/медвежий после реакции]\n\n"
            "💡 ВЫВОДЫ\n\n"
            "⚠️ Это не торговые сигналы.\n\n"
            "ВАЖНО: НЕ используй Markdown-таблицы, НЕ используй <br>,\n"
            "максимум 3500 символов."
        ),
    },
}


# ============================================================
# Логирование
# ============================================================
def log(msg: str, mode: str = "daily"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{mode}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ============================================================
# Сбор данных
# ============================================================
def collect_data() -> str:
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()
    offset = round((local_now - utc_now.replace(tzinfo=None)).total_seconds() / 3600)

    parts = []
    parts.append(f"📅 Дата: {utc_now.strftime('%Y-%m-%d')}")
    parts.append(f"🕐 UTC: {utc_now.strftime('%H:%M')}")
    parts.append(f"🕐 Локально (GMT+{offset}): {local_now.strftime('%H:%M')}")
    parts.append("")

    for sym in SYMBOLS:
        parts.append(f"=== {sym} ===")
        try:
            parts.append(mt5_summary(sym))
        except Exception as e:
            parts.append(f"[ERROR] {sym}: {e}")
        parts.append("")

    parts.append("=== 📰 ЭКОНОМИЧЕСКИЙ КАЛЕНДАРЬ ===")
    try:
        calendar = econ_calendar(countries=COUNTRIES, importance=IMPORTANCE, limit=10)
        parts.append(calendar)
    except Exception as e:
        parts.append(f"[ERROR] calendar: {e}")

    return "\n".join(parts)


# ============================================================
# Анализ
# ============================================================
def analyze_with_groq(data: str, mode: str) -> str:
    try:
        from providers.registry import get_provider
    except Exception as e:
        return f"[ERROR] Не могу получить Groq: {e}\n\n{data}"

    prompt_template = MODES[mode]["prompt"]
    prompt = prompt_template.format(data=data)

    try:
        provider = get_provider("groq")
        messages = [
            {"role": "system", "content": "Ты опытный финансовый аналитик. Пиши грамотно на русском."},
            {"role": "user", "content": prompt},
        ]
        result = provider.ask(
            model_name="openai/gpt-oss-20b",
            messages=messages,
            tools=None,
        )
        return result
    except Exception as e:
        return f"[ERROR] Groq: {e}\n\n{data}"


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="daily", choices=list(MODES.keys()))
    args = parser.parse_args()
    mode = args.mode

    title = MODES[mode]["title"]

    log("=" * 60, mode)
    log(f"БРИФИНГ [{mode}] — старт", mode)
    log("=" * 60, mode)

    total_start = time.time()

    # 1. Сбор данных
    log(f"[1/3] Сбор данных...", mode)
    t0 = time.time()
    try:
        data = collect_data()
        log(f"      OK ({time.time()-t0:.1f}с, {len(data)} символов)", mode)
    except Exception as e:
        log(f"      ОШИБКА: {type(e).__name__}: {e}", mode)
        log("БРИФИНГ ПРЕРВАН", mode)
        return

    # 2. Анализ
    log(f"[2/3] Анализ через Groq...", mode)
    t0 = time.time()
    try:
        briefing = analyze_with_groq(data, mode)
        log(f"      OK ({time.time()-t0:.1f}с, {len(briefing)} символов)", mode)
    except Exception as e:
        log(f"      ОШИБКА: {type(e).__name__}: {e}", mode)
        log("БРИФИНГ ПРЕРВАН", mode)
        return

    # 3. Отправка
    log(f"[3/3] Отправка в Telegram...", mode)
    t0 = time.time()
    try:
        result = telegram_send(briefing, title=title)
        log(f"      {result} ({time.time()-t0:.1f}с)", mode)
    except Exception as e:
        log(f"      ОШИБКА: {type(e).__name__}: {e}", mode)
        return

    log("=" * 60, mode)
    log(f"ГОТОВО (общее время: {time.time()-total_start:.1f}с)", mode)
    log("=" * 60, mode)


if __name__ == "__main__":
    main()