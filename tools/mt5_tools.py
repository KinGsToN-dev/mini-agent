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