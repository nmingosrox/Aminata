"""
Tick data access using MetaTrader5.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - handled at runtime
    mt5 = None


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


def get_ticks(symbol: str, start: Optional[datetime], count: int) -> List[Dict[str, Any]]:
    """
    Fetch historical tick data for a symbol from a start time.

    Args:
        symbol (str): The trading symbol (e.g., "EURUSD").
        start (datetime): The starting time for tick retrieval (UTC). If None, uses now - 1 day.
        count (int): Number of ticks to retrieve.

    Returns:
        list: A list of tick dictionaries with bid/ask/last prices and timestamps.
    """
    _ensure_mt5_initialized()
    if start is None:
        start = datetime.utcnow() - timedelta(days=1)
    ticks = mt5.copy_ticks_from(symbol, start, int(count), mt5.COPY_TICKS_ALL)
    if ticks is None:
        return []
    return [
        {
            "time": int(t[0]),
            "bid": float(t[1]),
            "ask": float(t[2]),
            "last": float(t[3]),
            "volume": float(t[4]),
            "time_msc": int(t[5]),
            "flags": int(t[6]),
            "volume_real": float(t[7]),
        }
        for t in ticks
    ]


def stream_ticks(symbol: str, start: Optional[datetime], count: int, batch_size: int = 10000) -> Iterable[List[Dict[str, Any]]]:
    """
    Stream ticks in batches for large backtests.

    Args:
        symbol (str): The trading symbol.
        start (datetime): The starting time for tick retrieval (UTC).
        count (int): Total number of ticks to stream.
        batch_size (int): Number of ticks per batch.

    Yields:
        list: Batches of tick dictionaries.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    remaining = int(count)
    cursor = start
    while remaining > 0:
        batch = get_ticks(symbol, cursor, min(batch_size, remaining))
        if not batch:
            break
        yield batch
        remaining -= len(batch)
        last_msc = batch[-1]["time_msc"]
        cursor = datetime.utcfromtimestamp(last_msc / 1000.0 + 0.001)


def write_ticks_memmap(path: str, ticks: List[Dict[str, Any]], dtype: Optional[np.dtype] = None) -> int:
    """
    Write tick data to a numpy memmap file.

    Args:
        path (str): Path to the memmap file.
        ticks (list): List of tick dictionaries.
        dtype (np.dtype): Optional dtype for the memmap array.

    Returns:
        int: Number of rows written.
    """
    if dtype is None:
        dtype = np.dtype(
            [
                ("time", "i8"),
                ("bid", "f8"),
                ("ask", "f8"),
                ("last", "f8"),
                ("volume", "f8"),
                ("time_msc", "i8"),
                ("flags", "i4"),
                ("volume_real", "f8"),
            ]
        )
    arr = np.memmap(path, dtype=dtype, mode="w+", shape=(len(ticks),))
    for i, t in enumerate(ticks):
        arr[i] = (
            int(t["time"]),
            float(t["bid"]),
            float(t["ask"]),
            float(t["last"]),
            float(t["volume"]),
            int(t["time_msc"]),
            int(t["flags"]),
            float(t["volume_real"]),
        )
    arr.flush()
    return len(ticks)


def open_ticks_memmap(path: str, dtype: np.dtype, mode: str = "r") -> np.memmap:
    """
    Open a numpy memmap containing tick data.

    Args:
        path (str): Path to the memmap file.
        dtype (np.dtype): dtype of the stored ticks.
        mode (str): Memmap mode, e.g., "r" or "r+".

    Returns:
        np.memmap: Memory-mapped numpy array of ticks.
    """
    return np.memmap(path, dtype=dtype, mode=mode)
