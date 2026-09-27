"""Торговые операции MT5 с тройной защитой.

Защита:
1. Demo-first: по умолчанию только demo-аккаунт
2. Лимит: не более MAX_LOT за одну операцию
3. Подтверждение: через callback (для интерактивных сессий)
4. Логирование: все операции в trades.log
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Конфиг и состояние
# ============================================================
PROJECT_DIR = Path(__file__).parent.parent
TRADES_LOG = PROJECT_DIR / "trades.log"
CONFIG_FILE = PROJECT_DIR / "trade_config.json"

# Значения по умолчанию
MAX_LOT = 0.1
ALLOW_LIVE = False

# Режим подтверждения: True — требует callback
CONFIRM_REQUIRED = True

# Глобальный callback для подтверждения (устанавливается из REPL)
_confirm_callback = None


# ============================================================
# Конфиг
# ============================================================
def _load_config():
    """Загружает trade_config.json."""
    global MAX_LOT, ALLOW_LIVE, CONFIRM_REQUIRED
    if not CONFIG_FILE.exists():
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        MAX_LOT = cfg.get("max_lot", MAX_LOT)
        ALLOW_LIVE = cfg.get("allow_live", ALLOW_LIVE)
        CONFIRM_REQUIRED = cfg.get("confirm_required", CONFIRM_REQUIRED)
    except Exception:
        pass


def _save_config():
    """Сохраняет trade_config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "max_lot": MAX_LOT,
                "allow_live": ALLOW_LIVE,
                "confirm_required": CONFIRM_REQUIRED,
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def set_max_lot(value: float):
    global MAX_LOT
    MAX_LOT = float(value)
    _save_config()


def set_allow_live(value: bool):
    global ALLOW_LIVE
    ALLOW_LIVE = bool(value)
    _save_config()


def set_confirm_required(value: bool):
    global CONFIRM_REQUIRED
    CONFIRM_REQUIRED = bool(value)
    _save_config()


def set_confirm_callback(cb):
    """Устанавливает callback для подтверждения ордера.
    cb(order_info: dict) -> bool
    """
    global _confirm_callback
    _confirm_callback = cb


def get_config_status() -> str:
    _load_config()
    return (
        f"MAX_LOT: {MAX_LOT}\n"
        f"ALLOW_LIVE: {ALLOW_LIVE}\n"
        f"CONFIRM_REQUIRED: {CONFIRM_REQUIRED}"
    )


# ============================================================
# Логирование
# ============================================================
def _log_trade(action: str, details: dict):
    """Пишет в trades.log."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(TRADES_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {action}: {json.dumps(details, ensure_ascii=False)}\n")
    except Exception:
        pass


# ============================================================
# Хелперы MT5
# ============================================================
def _mt5():
    """Импорт MT5 с проверкой."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return None, "[ERROR] MetaTrader5 не установлен"
    if not mt5.initialize():
        return None, "[ERROR] MT5 не запущен"
    return mt5, None


def _check_account(mt5, allow_live: bool = False) -> str | None:
    """Проверяет, что аккаунт — demo (или allow_live)."""
    acc = mt5.account_info()
    if acc is None:
        return "[ERROR] Не удалось получить данные аккаунта"
    
    trade_mode = acc.trade_mode
    # 0 = DEMO, 1 = CONTEST, 2 = REAL
    if trade_mode == 2 and not allow_live:
        return (
            f"[BLOCKED] Это LIVE-аккаунт (login {acc.login}). "
            f"Торговля заблокирована. Для разрешения: set_allow_live(True)"
        )
    return None


def _check_volume(mt5, symbol: str, volume: float) -> str | None:
    """Проверяет объём."""
    _load_config()
    if volume > MAX_LOT:
        return (
            f"[BLOCKED] Объём {volume} больше лимита {MAX_LOT}. "
            f"Изменить лимит: set_max_lot(<value>)"
        )
    
    info = mt5.symbol_info(symbol)
    if info is None:
        return f"[ERROR] Символ не найден: {symbol}"
    if volume < info.volume_min:
        return f"[ERROR] Объём {volume} меньше минимального {info.volume_min}"
    if volume > info.volume_max:
        return f"[ERROR] Объём {volume} больше максимального {info.volume_max}"
    # Проверяем шаг
    step = info.volume_step
    if step > 0 and abs(round(volume / step) * step - volume) > step / 2:
        return f"[ERROR] Объём {volume} не кратен шагу {step}"
    return None


# ============================================================
# Основные операции
# ============================================================
def _pick_filling_mode(mt5, symbol: str) -> int:
    """
    Возвращает подходящий filling mode для символа.
    info.filling_mode — битовая маска:
      1 = FOK разрешён
      2 = IOC разрешён
      4 = RETURN разрешён
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        return mt5.ORDER_FILLING_IOC

    flags = info.filling_mode
    if flags & 1:
        return mt5.ORDER_FILLING_FOK
    if flags & 2:
        return mt5.ORDER_FILLING_IOC
    if flags & 4:
        return mt5.ORDER_FILLING_RETURN
    # Fallback
    return mt5.ORDER_FILLING_IOC


def mt5_order(symbol: str, side: str, volume: float,
              sl: float = None, tp: float = None,
              comment: str = "mini-agent") -> str:
    """
    Размещает рыночный ордер.
    side: 'BUY' или 'SELL'
    sl/tp: цены (опционально)
    """
    _load_config()
    
    mt5, err = _mt5()
    if err:
        return err
    
    try:
        # 1. Проверка аккаунта
        err = _check_account(mt5, allow_live=ALLOW_LIVE)
        if err:
            _log_trade("ORDER_BLOCKED", {"reason": err, "symbol": symbol})
            return err
        
        # 2. Проверка объёма
        volume = float(volume)
        err = _check_volume(mt5, symbol, volume)
        if err:
            _log_trade("ORDER_BLOCKED", {"reason": err, "symbol": symbol, "volume": volume})
            return err
        
        # 3. Получаем tick
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return f"[ERROR] Не удалось получить tick для {symbol}"
        
        info = mt5.symbol_info(symbol)
        digits = info.digits
        filling = _pick_filling_mode(mt5, symbol)
        
        side_upper = side.upper()
        if side_upper == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif side_upper == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            return f"[ERROR] side должен быть BUY или SELL, не {side}"
        
        # 4. Подтверждение
        order_info = {
            "symbol": symbol,
            "side": side_upper,
            "volume": volume,
            "price": price,
            "sl": sl,
            "tp": tp,
            "account": mt5.account_info().login,
            "account_mode": "DEMO" if mt5.account_info().trade_mode == 0 else "LIVE",
        }
        
        if CONFIRM_REQUIRED and _confirm_callback is not None:
            if not _confirm_callback(order_info):
                _log_trade("ORDER_CANCELLED", order_info)
                return "[CANCELLED] Пользователь отклонил ордер"
        
        # 5. Формируем запрос
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 20260927,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)
        
        # 6. Отправляем
        result = mt5.order_send(request)
        if result is None:
            err_msg = f"[ERROR] order_send вернул None. Last error: {mt5.last_error()}"
            _log_trade("ORDER_FAILED", {**order_info, "error": err_msg})
            return err_msg
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            err_msg = (
                f"[ERROR] Ордер отклонён: retcode={result.retcode}, "
                f"comment={result.comment}"
            )
            _log_trade("ORDER_FAILED", {**order_info, "retcode": result.retcode, "comment": result.comment})
            return err_msg
        
        # 7. Успех
        _log_trade("ORDER_SUCCESS", {
            **order_info,
            "ticket": result.order,
            "deal": result.deal,
            "retcode": result.retcode,
        })
        
        return (
            f"[OK] Ордер размещён\n"
            f"  Ticket: {result.order}\n"
            f"  Deal: {result.deal}\n"
            f"  {side_upper} {volume} {symbol} @ {price}\n"
            f"  SL: {sl or 'нет'} | TP: {tp or 'нет'}"
        )
    except Exception as e:
        err_msg = f"[ERROR] {type(e).__name__}: {e}"
        _log_trade("ORDER_EXCEPTION", {"error": err_msg, "symbol": symbol})
        return err_msg
    finally:
        mt5.shutdown()


def mt5_close(ticket: int, comment: str = "close by mini-agent") -> str:
    """Закрывает позицию по ticket."""
    _load_config()
    
    mt5, err = _mt5()
    if err:
        return err
    
    try:
        err = _check_account(mt5, allow_live=ALLOW_LIVE)
        if err:
            return err
        
        # Получаем позицию
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return f"[ERROR] Позиция с ticket {ticket} не найдена"
        pos = positions[0]
        
        # Определяем тип закрытия
        if pos.type == 0:  # BUY
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(pos.symbol).bid
        else:  # SELL
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).ask
        
        # Подтверждение
        close_info = {
            "ticket": ticket,
            "symbol": pos.symbol,
            "side": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "price": price,
            "profit": pos.profit,
        }
        
        if CONFIRM_REQUIRED and _confirm_callback is not None:
            if not _confirm_callback(close_info):
                return "[CANCELLED] Закрытие отклонено"
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 20260927,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": _pick_filling_mode(mt5, pos.symbol),
        }
        
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err_msg = f"[ERROR] Не удалось закрыть: {result.retcode if result else 'None'}"
            _log_trade("CLOSE_FAILED", {**close_info, "error": err_msg})
            return err_msg
        
        _log_trade("CLOSE_SUCCESS", {**close_info, "order": result.order})
        return (
            f"[OK] Позиция закрыта\n"
            f"  Ticket: {ticket}\n"
            f"  {pos.symbol} {pos.volume} @ {price}\n"
            f"  Прибыль: {pos.profit:+.2f}"
        )
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


def mt5_close_all(comment: str = "close all by mini-agent") -> str:
    """Закрывает все позиции."""
    _load_config()
    
    mt5, err = _mt5()
    if err:
        return err
    
    try:
        err = _check_account(mt5, allow_live=ALLOW_LIVE)
        if err:
            return err
        
        positions = mt5.positions_get()
        if not positions:
            return "Открытых позиций нет"
        
        if CONFIRM_REQUIRED and _confirm_callback is not None:
            total_profit = sum(p.profit for p in positions)
            close_info = {
                "action": "CLOSE_ALL",
                "count": len(positions),
                "total_profit": total_profit,
            }
            if not _confirm_callback(close_info):
                return "[CANCELLED] Закрытие всех отклонено"
        
        mt5.shutdown()
        # Перезапускаем чтобы закрывать по одной
        results = []
        for pos in positions:
            res = mt5_close(pos.ticket, comment)
            results.append(res)
        
        success = sum(1 for r in results if r.startswith("[OK]"))
        return f"[OK] Закрыто {success} из {len(positions)}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def mt5_modify(ticket: int, sl: float = None, tp: float = None) -> str:
    """Изменяет SL/TP существующей позиции."""
    _load_config()
    
    mt5, err = _mt5()
    if err:
        return err
    
    try:
        err = _check_account(mt5, allow_live=ALLOW_LIVE)
        if err:
            return err
        
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return f"[ERROR] Позиция {ticket} не найдена"
        pos = positions[0]
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": pos.symbol,
        }
        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)
        
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            return f"[ERROR] Изменение отклонено: {result.retcode if result else 'None'}"
        
        _log_trade("MODIFY_SUCCESS", {
            "ticket": ticket,
            "sl": sl,
            "tp": tp,
        })
        return f"[OK] Позиция {ticket} изменена: SL={sl}, TP={tp}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()


def mt5_pending(symbol: str, side: str, price: float, volume: float,
                sl: float = None, tp: float = None,
                comment: str = "pending by mini-agent") -> str:
    """
    Отложенный ордер.
    side: 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP'
    """
    _load_config()
    
    mt5, err = _mt5()
    if err:
        return err
    
    try:
        err = _check_account(mt5, allow_live=ALLOW_LIVE)
        if err:
            return err
        
        volume = float(volume)
        err = _check_volume(mt5, symbol, volume)
        if err:
            return err
        
        side_map = {
            "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
            "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
            "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
            "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
        }
        if side.upper() not in side_map:
            return f"[ERROR] side должен быть один из: {list(side_map.keys())}"
        
        info = mt5.symbol_info(symbol)
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": side_map[side.upper()],
            "price": float(price),
            "deviation": 20,
            "magic": 20260927,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": _pick_filling_mode(mt5, symbol),
        }
        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)
        
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            return f"[ERROR] Отложенный ордер отклонён: {result.retcode if result else 'None'}"
        
        _log_trade("PENDING_SUCCESS", {
            "symbol": symbol, "side": side, "price": price, "volume": volume,
            "ticket": result.order,
        })
        return f"[OK] Отложенный ордер: ticket {result.order}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
    finally:
        mt5.shutdown()