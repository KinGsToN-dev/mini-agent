"""Инструменты MetaTrader 5 — только чтение (безопасно)."""
from datetime import datetime


TIMEFRAMES = {
    "M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30", "H1": "TIMEFRAME_H1", "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1", "W1": "TIMEFRAME_W1", "MN1": "TIMEFRAME_MN1",
}


def _mt5():
    """Импорт MT5 с проверкой."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return None, "[ERROR] MetaTrader5 не установлен. pip install MetaTrader5"
    if not mt5.initialize():
        return None, "[ERROR] MT5 не запущен или терминал не отвечает"
    return mt5, None


def mt5_quote(symbol: str) -> str:
    """Текущая котировка (bid/ask) для символа."""
    mt5, err = _mt5()
    if err:
        return err
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return f"[ERROR] Символ не найден: {symbol}. Проверь название."
        info = mt5.symbol_info(symbol)
        spread = round((tick.ask - tick.bid) * (10 ** info.digits), 1) if info else "?"
        return (
            f"{symbol}\n"
            f"  Bid: {tick.bid}\n"
            f"  Ask: {tick.ask}\n"
            f"  Spread: {spread} пипсов\n"
            f"  Время: {datetime.fromtimestamp(tick.time).strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


def mt5_bars(symbol: str, timeframe: str = "H1", count: int = 20) -> str:
    """OHLC-свечи. timeframe: M1, M5, M15, M30, H1, H4, D1, W1, MN1."""
    mt5, err = _mt5()
    if err:
        return err
    try:
        tf_name = TIMEFRAMES.get(timeframe.upper())
        if not tf_name:
            return f"[ERROR] Неверный timeframe: {timeframe}. Доступно: {list(TIMEFRAMES)}"
        tf = getattr(mt5, tf_name)

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, min(count, 100))
        if rates is None or len(rates) == 0:
            return f"[ERROR] Нет данных для {symbol} {timeframe}"

        lines = [f"{symbol} {timeframe} (последние {len(rates)} свечей):",
                 "  time                 open      high      low       close     vol"]
        for r in rates[-10:]:  # Последние 10 для читаемости
            t = datetime.fromtimestamp(r["time"]).strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"  {t}  {r['open']:>8.5f}  {r['high']:>8.5f}  "
                f"{r['low']:>8.5f}  {r['close']:>8.5f}  {r['tick_volume']:>6}"
            )
        if len(rates) > 10:
            lines.append(f"  ...[всего {len(rates)} свечей]")
        return "\n".join(lines)
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


def mt5_account() -> str:
    """Информация об аккаунте: баланс, equity, маржа."""
    mt5, err = _mt5()
    if err:
        return err
    try:
        acc = mt5.account_info()
        if acc is None:
            return "[ERROR] Аккаунт не подключён"
        return (
            f"Аккаунт: {acc.login} ({acc.server})\n"
            f"  Валюта: {acc.currency}\n"
            f"  Баланс: {acc.balance:.2f}\n"
            f"  Equity: {acc.equity:.2f}\n"
            f"  Маржа: {acc.margin:.2f}\n"
            f"  Свободная маржа: {acc.margin_free:.2f}\n"
            f"  Уровень маржи: {acc.margin_level:.1f}%\n"
            f"  Прибыль: {acc.profit:.2f}"
        )
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


def mt5_positions() -> str:
    """Список открытых позиций."""
    mt5, err = _mt5()
    if err:
        return err
    try:
        positions = mt5.positions_get()
        if not positions:
            return "Открытых позиций нет"
        lines = [f"Открытых позиций: {len(positions)}",
                 "  ticket    symbol     type   volume   open       current    profit"]
        for p in positions:
            side = "BUY" if p.type == 0 else "SELL"
            lines.append(
                f"  {p.ticket:<9} {p.symbol:<10} {side:<5} "
                f"{p.volume:<8.2f} {p.price_open:<10.5f} {p.price_current:<10.5f} "
                f"{p.profit:>+8.2f}"
            )
        total = sum(p.profit for p in positions)
        lines.append(f"\nОбщая прибыль: {total:+.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()

def mt5_summary(symbol: str) -> str:
    """
    Сводка по символу: цена + изменение за 24ч + диапазон + MA(20) + MA(50).
    Используй для быстрого анализа тренда.
    """
    mt5, err = _mt5()
    if err:
        return err
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return f"[ERROR] Символ не найден: {symbol}"

        info = mt5.symbol_info(symbol)
        digits = info.digits if info else 5
        point = 10 ** (-digits)

        # Последние 100 свечей H1 для индикаторов
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 50:
            return f"[ERROR] Недостаточно данных для {symbol}"

        closes = [float(r["close"]) for r in rates]
        highs = [float(r["high"]) for r in rates]
        lows = [float(r["low"]) for r in rates]

        # Текущая цена
        bid = tick.bid
        ask = tick.ask
        spread = round((ask - bid) / point, 1)

        # 24 часа назад (24 свечи H1)
        if len(closes) >= 24:
            price_24h_ago = closes[-24]
            change_24h = bid - price_24h_ago
            change_24h_pct = (change_24h / price_24h_ago) * 100
        else:
            change_24h = 0
            change_24h_pct = 0

        # Диапазон за 24ч
        high_24h = max(highs[-24:]) if len(highs) >= 24 else max(highs)
        low_24h = min(lows[-24:]) if len(lows) >= 24 else min(lows)

        # MA(20) и MA(50)
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50

        # Простой RSI(14)
        rsi = _rsi(closes, 14)

        # Тренд
        if bid > ma20 > ma50:
            trend = "ВОСХОДЯЩИЙ (цена > MA20 > MA50)"
        elif bid < ma20 < ma50:
            trend = "НИСХОДЯЩИЙ (цена < MA20 < MA50)"
        else:
            trend = "БОКОВОЙ / НЕОПРЕДЕЛЁННЫЙ"

        return (
            f"{symbol} — сводка\n"
            f"\n"
            f"💰 Цена: {bid:.{digits}f} / {ask:.{digits}f} (spread {spread})\n"
            f"📊 Изменение 24ч: {change_24h:+.{digits}f} ({change_24h_pct:+.2f}%)\n"
            f"📈 Диапазон 24ч: {low_24h:.{digits}f} — {high_24h:.{digits}f}\n"
            f"\n"
            f"📉 Индикаторы H1:\n"
            f"   MA(20): {ma20:.{digits}f}\n"
            f"   MA(50): {ma50:.{digits}f}\n"
            f"   RSI(14): {rsi:.1f}\n"
            f"\n"
            f"🎯 Тренд: {trend}\n"
            f"\n"
            f"💡 Подсказки для анализа:\n"
            f"   - RSI > 70: перекупленность\n"
            f"   - RSI < 30: перепроданность\n"
            f"   - Цена выше MA20/MA50: bullish\n"
            f"   - Цена ниже MA20/MA50: bearish"
        )
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


def _rsi(closes: list, period: int = 14) -> float:
    """Простой расчёт RSI."""
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
    # Берём последние `period` значений
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))