from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - handled at runtime
    mt5 = None


class TickDataFetcher:
    """
    Provide tick-level data. In dev mode, returns synthetic ticks.
    In prod mode, uses MetaTrader5 terminal.
    """

    def fetch_ticks(
        self,
        symbol: str,
        count: int = 100,
        mode: str = "dev",
        start: Optional[datetime] = None,
    ) -> List[Dict]:
        if not symbol:
            raise ValueError("symbol must be a non-empty string")
        if count <= 0:
            raise ValueError("count must be positive")
        if mode not in {"dev", "prod"}:
            raise ValueError("mode must be 'dev' or 'prod'")

        if mode == "prod":
            if mt5 is None:
                raise RuntimeError("MetaTrader5 package is not installed.")
            if not mt5.initialize():
                err = mt5.last_error()
                raise RuntimeError(f"MetaTrader5 initialize failed: {err}")
            if start is None:
                start = datetime.utcnow() - timedelta(days=1)
            ticks = mt5.copy_ticks_from(symbol, start, int(count), mt5.COPY_TICKS_ALL)
            if ticks is None:
                return []
            return [
                {
                    "time": datetime.utcfromtimestamp(int(t[0])),
                    "bid": float(t[1]),
                    "ask": float(t[2]),
                    "volume": float(t[4]),
                }
                for t in ticks
            ]

        now = datetime.utcnow()
        ticks = []
        price = 1.1000
        for i in range(count):
            price += 0.00001
            ticks.append(
                {
                    "time": now,
                    "bid": price - 0.0001,
                    "ask": price + 0.0001,
                    "volume": 100 + i,
                }
            )
        return ticks


if __name__ == "__main__":
    fetcher = TickDataFetcher()
    print(fetcher.fetch_ticks("EURUSD", count=5, mode="dev"))
