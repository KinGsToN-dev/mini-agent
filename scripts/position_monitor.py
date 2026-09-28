"""
Мониторинг открытых позиций MT5.

Запускается Task Scheduler каждый час.
Если есть позиции — отправляет отчёт в Telegram.
Если нет — молчит.
Если P&L не изменился с прошлого запуска — молчит.

Запуск вручную: python scripts/position_monitor.py
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from tools.mt5_tools import mt5_positions, mt5_account
from tools.telegram_tools import telegram_send


# ============================================================
# Пути и конфиг
# ============================================================
PROJECT_DIR = Path(__file__).parent.parent
STATE_FILE = PROJECT_DIR / "positions_state.json"
LOG_FILE = PROJECT_DIR / "position_monitor.log"


# ============================================================
# Логирование
# ============================================================
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        from agent.log import log
        log(f"position_monitor: log write failed: {type(e).__name__}: {e}", level="WARNING")


# ============================================================
# Состояние
# ============================================================
def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        from agent.log import log
        log(f"position_monitor: load_state failed: {type(e).__name__}: {e}", level="WARNING")
        return {}


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Не удалось сохранить state: {e}")


# ============================================================
# Парсинг позиций
# ============================================================
def parse_positions() -> tuple:
    """
    Возвращает (positions_list, total_profit, raw_text).
    positions_list — список dict {ticket, symbol, side, volume, open, current, profit}
    """
    import MetaTrader5 as mt5

    if not mt5.initialize():
        return [], 0, "MT5 не запущен"

    try:
        positions = mt5.positions_get()
        if not positions:
            return [], 0, "Нет открытых позиций"

        result = []
        for p in positions:
            result.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "side": "BUY" if p.type == 0 else "SELL",
                "volume": p.volume,
                "open": p.price_open,
                "current": p.price_current,
                "profit": p.profit,
            })
        total = sum(p["profit"] for p in result)
        return result, total, "OK"
    except Exception as e:
        return [], 0, f"Ошибка: {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


# ============================================================
# Формирование отчёта
# ============================================================
def format_report(positions: list, total_profit: float) -> str:
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()
    offset = round((local_now - utc_now.replace(tzinfo=None)).total_seconds() / 3600)

    lines = []
    lines.append("💼 МОНИТОРИНГ ПОЗИЦИЙ")
    lines.append(f"{utc_now.strftime('%Y-%m-%d %H:%M UTC')} "
                 f"({local_now.strftime('%H:%M')} GMT+{offset})")
    lines.append("")
    lines.append(f"📊 Открытых позиций: {len(positions)}")
    lines.append("")

    for p in positions:
        profit_emoji = "🟢" if p["profit"] >= 0 else "🔴"
        lines.append(f"{profit_emoji} **{p['symbol']}** {p['side']} {p['volume']}")
        lines.append(f"   Открытие: {p['open']:.5f}")
        lines.append(f"   Текущая:  {p['current']:.5f}")
        lines.append(f"   P&L:      {p['profit']:+.2f}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("💰 **АККАУНТ:**")

    # Добавляем данные аккаунта
    account_text = mt5_account()
    for line in account_text.split("\n"):
        lines.append(f"   {line.strip()}")

    lines.append("")
    lines.append(f"📈 **Общая прибыль: {total_profit:+.2f}**")

    return "\n".join(lines)


# ============================================================
# Главная логика
# ============================================================
def main():
    log("=" * 60)
    log("МОНИТОРИНГ ПОЗИЦИЙ — старт")
    log("=" * 60)

    t0 = time.time()

    # 1. Получаем позиции
    positions, total_profit, status = parse_positions()
    log(f"[1/3] Позиций: {len(positions)}, общий P&L: {total_profit:+.2f} ({status})")

    # 2. Если нет позиций — молчим
    if not positions:
        log("[2/3] Нет позиций — выходим без отправки")
        log("=" * 60)
        return

    # 3. Проверяем изменение с прошлого запуска
    state = load_state()
    prev_profit = state.get("total_profit")
    prev_count = state.get("count", 0)

    # Если P&L не изменился И количество позиций то же — молчим
    if prev_profit is not None and abs(prev_profit - total_profit) < 0.01 and prev_count == len(positions):
        log(f"[3/3] P&L не изменился ({total_profit:+.2f}) — выходим без отправки")
        log("=" * 60)
        return

    log(f"[3/3] P&L изменился: {prev_profit} → {total_profit:+.2f} — отправляем")

    # 4. Формируем отчёт и отправляем
    try:
        report = format_report(positions, total_profit)
        result = telegram_send(report, title="💼 Мониторинг позиций")
        log(f"      {result}")
    except Exception as e:
        log(f"      ОШИБКА отправки: {type(e).__name__}: {e}")
        return

    # 5. Сохраняем новое состояние
    save_state({
        "total_profit": total_profit,
        "count": len(positions),
        "updated": datetime.now(timezone.utc).isoformat(),
    })

    log("=" * 60)
    log(f"ГОТОВО (общее время: {time.time()-t0:.1f}с)")
    log("=" * 60)


if __name__ == "__main__":
    main()