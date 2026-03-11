"""
Candle data access using MetaTrader5.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - handled at runtime
    mt5 = None

_TIMEFRAME_MAP = {
    "M1": lambda: mt5.TIMEFRAME_M1,
    "M2": lambda: mt5.TIMEFRAME_M2,
    "M3": lambda: mt5.TIMEFRAME_M3,
    "M4": lambda: mt5.TIMEFRAME_M4,
    "M5": lambda: mt5.TIMEFRAME_M5,
    "M6": lambda: mt5.TIMEFRAME_M6,
    "M10": lambda: mt5.TIMEFRAME_M10,
    "M12": lambda: mt5.TIMEFRAME_M12,
    "M15": lambda: mt5.TIMEFRAME_M15,
    "M20": lambda: mt5.TIMEFRAME_M20,
    "M30": lambda: mt5.TIMEFRAME_M30,
    "H1": lambda: mt5.TIMEFRAME_H1,
    "H2": lambda: mt5.TIMEFRAME_H2,
    "H3": lambda: mt5.TIMEFRAME_H3,
    "H4": lambda: mt5.TIMEFRAME_H4,
    "H6": lambda: mt5.TIMEFRAME_H6,
    "H8": lambda: mt5.TIMEFRAME_H8,
    "H12": lambda: mt5.TIMEFRAME_H12,
    "D1": lambda: mt5.TIMEFRAME_D1,
    "W1": lambda: mt5.TIMEFRAME_W1,
    "MN1": lambda: mt5.TIMEFRAME_MN1,
}


def _ensure_mt5_initialized():
    """
    Ensure the MetaTrader5 terminal is initialized.

    Raises:
        RuntimeError: If MetaTrader5 is not installed or initialization fails.
    """
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not installed.")
    if not mt5.initialize():
        err = mt5.last_error()
        raise RuntimeError(f"MetaTrader5 initialize failed: {err}")


def _resolve_timeframe(timeframe: Any) -> int:
    """
    Resolve timeframe input to a MetaTrader5 timeframe constant.

    Args:
        timeframe (Any): A MetaTrader5 timeframe constant or a string like "M15".

    Returns:
        int: MetaTrader5 timeframe constant.

    Raises:
        ValueError: If the timeframe cannot be resolved.
    """
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not installed.")
    if isinstance(timeframe, int):
        return timeframe
    if isinstance(timeframe, str):
        key = timeframe.strip().upper()
        if key in _TIMEFRAME_MAP:
            return _TIMEFRAME_MAP[key]()
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def get_candles(symbol: str, timeframe: Any, count: int) -> List[Dict[str, Any]]:
    """
    Fetch historical OHLC bars for a given symbol.

    Args:
        symbol (str): The trading symbol (e.g., "EURUSD").
        timeframe (Any): MT5 timeframe constant or string like "M15".
        count (int): Number of historical bars to retrieve.

    Returns:
        list: A list of bar dictionaries with keys like time, open, high, low, close.
    """
    _ensure_mt5_initialized()
    tf = _resolve_timeframe(timeframe)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, int(count))
    if rates is None:
        return []
    return [
        {
            "time": int(r[0]),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "tick_volume": int(r[5]),
            "spread": int(r[6]),
            "real_volume": int(r[7]),
        }
        for r in rates
    ]


def get_close_series(symbol: str, timeframe: Any, count: int) -> List[float]:
    """
    Fetch a list of close prices for a given symbol.

    Args:
        symbol (str): The trading symbol.
        timeframe (Any): MT5 timeframe constant or string like "M15".
        count (int): Number of bars to retrieve.

    Returns:
        list: Close prices in chronological order.
    """
    bars = get_candles(symbol, timeframe, count)
    return [b["close"] for b in bars]
