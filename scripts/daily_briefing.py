"""
Утренний брифинг по расписанию.

Запускается Windows Task Scheduler в 09:00 (GMT+5 = 04:00 UTC).
Собирает данные из MT5 и Biquote, отправляет анализ в Telegram через Groq.

Запуск вручную: python scripts/daily_briefing.py
"""
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Добавляем корень проекта в path
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
TITLE = "🌅 Утренний брифинг"


# ============================================================
# Сбор данных
# ============================================================
def collect_data() -> str:
    """Собирает данные по всем символам + экономический календарь."""
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()

    parts = []
    parts.append(f"📅 Дата: {utc_now.strftime('%Y-%m-%d')}")
    parts.append(f"🕐 UTC: {utc_now.strftime('%H:%M')}")
    parts.append(f"🕐 Локально (GMT+5): {local_now.strftime('%H:%M')}")
    parts.append("")

    # Сводки по каждому символу
    for sym in SYMBOLS:
        parts.append(f"=== {sym} ===")
        try:
            summary = mt5_summary(sym)
            parts.append(summary)
        except Exception as e:
            parts.append(f"[ERROR] {sym}: {e}")
        parts.append("")

    # Экономический календарь
    parts.append("=== 📰 ЭКОНОМИЧЕСКИЙ КАЛЕНДАРЬ ===")
    try:
        calendar = econ_calendar(
            countries=COUNTRIES,
            importance=IMPORTANCE,
            limit=10,
        )
        parts.append(calendar)
    except Exception as e:
        parts.append(f"[ERROR] calendar: {e}")

    return "\n".join(parts)


# ============================================================
# Анализ через Groq
# ============================================================
def analyze_with_groq(data: str) -> str:
    """Отправляет данные в Groq для профессионального анализа."""
    try:
        from providers.registry import get_provider
    except Exception as e:
        return f"[ERROR] Не могу получить Groq: {e}\n\n{data}"

    prompt = f"""Ты — опытный финансовый аналитик. Напиши утренний брифинг для Telegram.

ДАННЫЕ:
{data}

ФОРМАТ (для Telegram, БЕЗ таблиц Markdown):

🌅 УТРЕННИЙ БРИФИНГ
[дата, время UTC / GMT+5]

━━━━━━━━━━━━━━━━━━━━━━━━

📊 КРАТКАЯ СВОДКА

**BTCUSD** — $[цена]
Тренд: [восходящий/нисходящий/боковой]
Изменение 24ч: [+/-X%]

**XAUUSD** — $[цена]
Тренд: ...
Изменение 24ч: ...

**EURUSD** — $[цена]
Тренд: ...
Изменение 24ч: ...

━━━━━━━━━━━━━━━━━━━━━━━━

📈 ТЕХНИЧЕСКИЙ АНАЛИЗ

**BTCUSD**
• Поддержка: MA20 = $X, MA50 = $Y
• Сопротивление: $Z
• RSI(14): [значение] — [интерпретация]

**XAUUSD**
• ...
• ...

**EURUSD**
• ...
• ...

━━━━━━━━━━━━━━━━━━━━━━━━

📰 МАКРО КАЛЕНДАРЬ

**28 сентября** (завтра)
• 13:30 UTC (18:30 GMT+5) — Речь Лагард (EUR)
• 14:00 UTC (19:00 GMT+5) — CB Consumer Confidence (USD)

**29 сентября**
• ...

━━━━━━━━━━━━━━━━━━━━━━━━

🎯 СЦЕНАРИИ

**BTCUSD**
🐂 Бычий: [описание]
🐻 Медвежий: [описание]

**XAUUSD**
🐂 Бычий: ...
🐻 Медвежий: ...

**EURUSD**
🐂 Бычий: ...
🐻 Медвежий: ...

━━━━━━━━━━━━━━━━━━━━━━━━

💡 ВЫВОДЫ

• BTC: [краткий вывод]
• XAU: [краткий вывод]
• EUR: [краткий вывод]

⚠️ Это не торговые сигналы. Риск-менеджмент обязателен.

КРИТИЧЕСКИ ВАЖНО:
- НЕ используй Markdown-таблицы (| ... |) — Telegram их не поддерживает
- НЕ используй HTML-теги <br> — используй реальные переносы строк
- Максимум 3500 символов (лимит Telegram 4096)
- Пиши грамотно на русском
- Давай рекомендации, НЕ сигналы
- Экономь место, но не в ущерб содержанию
"""

    try:
        provider = get_provider("groq")
        # Сообщения в OpenAI формате
        messages = [
            {"role": "system", "content": "Ты опытный финансовый аналитик. Пиши грамотно на русском."},
            {"role": "user", "content": prompt},
        ]
        result = provider.ask(
            model_name="openai/gpt-oss-20b",
            messages=messages,
            tools=None,  # Без tools для скорости
        )
        return result
    except Exception as e:
        return f"[ERROR] Groq: {e}\n\n{data}"


# ============================================================
# Main
# ============================================================
# ============================================================
# Логирование
# ============================================================
from pathlib import Path as _Path
LOG_FILE = _Path(__file__).parent.parent / "briefing.log"


def log(msg: str):
    """Пишет в лог с timestamp."""
    from datetime import datetime as _dt
    ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main():
    log("=" * 60)
    log("УТРЕННИЙ БРИФИНГ — старт")
    log("=" * 60)

    total_start = time.time()

    # 1. Сбор данных
    log("[1/3] Сбор данных...")
    t0 = time.time()
    try:
        data = collect_data()
        log(f"      OK ({time.time()-t0:.1f}с, {len(data)} символов)")
    except Exception as e:
        log(f"      ОШИБКА: {type(e).__name__}: {e}")
        log("БРИФИНГ ПРЕРВАН")
        return

    # 2. Анализ через Groq
    log("[2/3] Анализ через Groq...")
    t0 = time.time()
    try:
        briefing = analyze_with_groq(data)
        log(f"      OK ({time.time()-t0:.1f}с, {len(briefing)} символов)")
    except Exception as e:
        log(f"      ОШИБКА: {type(e).__name__}: {e}")
        log("БРИФИНГ ПРЕРВАН")
        return

    # 3. Отправка в Telegram
    log("[3/3] Отправка в Telegram...")
    t0 = time.time()
    try:
        result = telegram_send(briefing, title=TITLE)
        log(f"      {result} ({time.time()-t0:.1f}с)")
    except Exception as e:
        log(f"      ОШИБКА: {type(e).__name__}: {e}")
        log("БРИФИНГ ПРЕРВАН")
        return

    log("=" * 60)
    log(f"ГОТОВО (общее время: {time.time()-total_start:.1f}с)")
    log("=" * 60)


if __name__ == "__main__":
    main()