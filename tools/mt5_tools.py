"""Инструменты MetaTrader 5 — только чтение (безопасно)."""
from datetime import datetime, timezone

from tools._deps import ensure_mt5_running


TIMEFRAMES = {
    "M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30", "H1": "TIMEFRAME_H1", "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1", "W1": "TIMEFRAME_W1", "MN1": "TIMEFRAME_MN1",
}


def _mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return None, "[ERROR] MetaTrader5 не установлен. pip install MetaTrader5"
    if not mt5.initialize():
        return None, "[ERROR] MT5 не запущен или терминал не отвечает"
    return mt5, None


def _fmt_utc_time():
    """Возвращает строку с UTC и локальным временем."""
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()
    offset = round((local_now - utc_now.replace(tzinfo=None)).total_seconds() / 3600)
    return (
        utc_now.strftime("%Y-%m-%d %H:%M UTC")
        + " (локально "
        + local_now.strftime("%H:%M")
        + " GMT+"
        + str(offset)
        + ")"
    )


def mt5_quote(symbol: str) -> str:
    ok, msg = ensure_mt5_running()
    if not ok:
        return f"[ERROR] MT5 unavailable: {msg}"
    mt5, err = _mt5()
    if err:
        return err
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return "[ERROR] Символ не найден: " + symbol
        info = mt5.symbol_info(symbol)
        spread = round((tick.ask - tick.bid) * (10 ** info.digits), 1) if info else "?"
        return (
            symbol + "\n"
            "  Bid: " + str(tick.bid) + "\n"
            "  Ask: " + str(tick.ask) + "\n"
            "  Spread: " + str(spread) + " пипсов\n"
            "  Время: " + datetime.fromtimestamp(tick.time).strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        return "[ERROR] " + type(e).__name__ + ": " + str(e)
    finally:
        mt5.shutdown()


def mt5_bars(symbol: str, timeframe: str = "H1", count: int = 20) -> str:
    ok, msg = ensure_mt5_running()
    if not ok:
        return f"[ERROR] MT5 unavailable: {msg}"
    mt5, err = _mt5()
    if err:
        return err
    try:
        tf_name = TIMEFRAMES.get(timeframe.upper())
        if not tf_name:
            return "[ERROR] Неверный timeframe: " + timeframe
        tf = getattr(mt5, tf_name)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, min(count, 100))
        if rates is None or len(rates) == 0:
            return "[ERROR] Нет данных для " + symbol + " " + timeframe
        lines = [symbol + " " + timeframe + " (последние " + str(len(rates)) + " свечей):",
                 "  time                 open      high      low       close     vol"]
        for r in rates[-10:]:
            t = datetime.fromtimestamp(r["time"]).strftime("%Y-%m-%d %H:%M")
            lines.append(
                "  " + t + "  " + f"{r['open']:>8.5f}  {r['high']:>8.5f}  "
                + f"{r['low']:>8.5f}  {r['close']:>8.5f}  {r['tick_volume']:>6}"
            )
        if len(rates) > 10:
            lines.append("  ...[всего " + str(len(rates)) + " свечей]")
        return "\n".join(lines)
    except Exception as e:
        return "[ERROR] " + type(e).__name__ + ": " + str(e)
    finally:
        mt5.shutdown()


def mt5_account() -> str:
    ok, msg = ensure_mt5_running()
    if not ok:
        return f"[ERROR] MT5 unavailable: {msg}"
    mt5, err = _mt5()
    if err:
        return err
    try:
        acc = mt5.account_info()
        if acc is None:
            return "[ERROR] Аккаунт не подключён"
        return (
            "Аккаунт: " + str(acc.login) + " (" + str(acc.server) + ")\n"
            "  Валюта: " + str(acc.currency) + "\n"
            "  Баланс: " + f"{acc.balance:.2f}" + "\n"
            "  Equity: " + f"{acc.equity:.2f}" + "\n"
            "  Маржа: " + f"{acc.margin:.2f}" + "\n"
            "  Свободная маржа: " + f"{acc.margin_free:.2f}" + "\n"
            "  Уровень маржи: " + f"{acc.margin_level:.1f}" + "%\n"
            "  Прибыль: " + f"{acc.profit:.2f}"
        )
    except Exception as e:
        return "[ERROR] " + type(e).__name__ + ": " + str(e)
    finally:
        mt5.shutdown()


def mt5_positions() -> str:
    ok, msg = ensure_mt5_running()
    if not ok:
        return f"[ERROR] MT5 unavailable: {msg}"
    mt5, err = _mt5()
    if err:
        return err
    try:
        positions = mt5.positions_get()
        if not positions:
            return "Открытых позиций нет"
        lines = ["Открытых позиций: " + str(len(positions)),
                 "  ticket    symbol     type   volume   open       current    profit"]
        for p in positions:
            side = "BUY" if p.type == 0 else "SELL"
            lines.append(
                "  " + f"{p.ticket:<9}" + " " + f"{p.symbol:<10}" + " "
                + f"{side:<5}" + " " + f"{p.volume:<8.2f}" + " "
                + f"{p.price_open:<10.5f}" + " " + f"{p.price_current:<10.5f}" + " "
                + f"{p.profit:>+8.2f}"
            )
        total = sum(p.profit for p in positions)
        lines.append("\nОбщая прибыль: " + f"{total:+.2f}")
        return "\n".join(lines)
    except Exception as e:
        return "[ERROR] " + type(e).__name__ + ": " + str(e)
    finally:
        mt5.shutdown()


def _rsi(closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-diff)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def mt5_summary(symbol: str) -> str:
    ok, msg = ensure_mt5_running()
    if not ok:
        return f"[ERROR] MT5 unavailable: {msg}"
    mt5, err = _mt5()
    if err:
        return err
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return "[ERROR] Символ не найден: " + symbol

        info = mt5.symbol_info(symbol)
        digits = info.digits if info else 5
        point = 10 ** (-digits)

        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 50:
            return "[ERROR] Недостаточно данных для " + symbol

        closes = [float(r["close"]) for r in rates]
        highs = [float(r["high"]) for r in rates]
        lows = [float(r["low"]) for r in rates]

        bid = tick.bid
        ask = tick.ask
        spread = round((ask - bid) / point, 1)

        if len(closes) >= 24:
            price_24h_ago = closes[-24]
            change_24h = bid - price_24h_ago
            change_24h_pct = (change_24h / price_24h_ago) * 100
        else:
            change_24h = 0
            change_24h_pct = 0

        high_24h = max(highs[-24:]) if len(highs) >= 24 else max(highs)
        low_24h = min(lows[-24:]) if len(lows) >= 24 else min(lows)

        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50
        rsi = _rsi(closes, 14)

        if bid > ma20 > ma50:
            trend = "ВОСХОДЯЩИЙ (цена > MA20 > MA50)"
        elif bid < ma20 < ma50:
            trend = "НИСХОДЯЩИЙ (цена < MA20 < MA50)"
        else:
            trend = "БОКОВОЙ / НЕОПРЕДЕЛЁННЫЙ"

        price_str = f"{bid:.{digits}f} / {ask:.{digits}f}"
        change_str = f"{change_24h:+.{digits}f} ({change_24h_pct:+.2f}%)"
        range_str = f"{low_24h:.{digits}f} - {high_24h:.{digits}f}"
        ma20_str = f"{ma20:.{digits}f}"
        ma50_str = f"{ma50:.{digits}f}"
        rsi_str = f"{rsi:.1f}"

        return (
            symbol + " - сводка\n"
            + "Время: " + _fmt_utc_time() + "\n"
            + "\n"
            + "Цена: " + price_str + " (spread " + str(spread) + ")\n"
            + "Изменение 24ч: " + change_str + "\n"
            + "Диапазон 24ч: " + range_str + "\n"
            + "\n"
            + "Индикаторы H1:\n"
            + "   MA(20): " + ma20_str + "\n"
            + "   MA(50): " + ma50_str + "\n"
            + "   RSI(14): " + rsi_str + "\n"
            + "\n"
            + "Тренд: " + trend + "\n"
            + "\n"
            + "Подсказки:\n"
            + "   - RSI > 70: перекупленность\n"
            + "   - RSI < 30: перепроданность\n"
            + "   - Цена выше MA20/MA50: bullish\n"
            + "   - Цена ниже MA20/MA50: bearish"
        )
    except Exception as e:
        return "[ERROR] " + type(e).__name__ + ": " + str(e)
    finally:
        mt5.shutdown()
