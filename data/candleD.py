from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional

import pandas as pd


class CandleDataFetcher:
    """
    Provide OHLC data. In dev mode, returns synthetic candles.
    In prod mode, implement real broker/feed integration.
    """

    def fetch_ohlc(
        self,
        symbol: str,
        count: int = 200,
        mode: str = "dev",
        csv_path: Optional[str] = None,
    ) -> pd.DataFrame:
        if not symbol:
            raise ValueError("symbol must be a non-empty string")
        if count <= 0:
            raise ValueError("count must be positive")
        if mode not in {"dev", "prod"}:
            raise ValueError("mode must be 'dev' or 'prod'")

        if mode == "prod":
            if not csv_path:
                raise NotImplementedError(
                    "Candle data feed not configured. Provide csv_path or integrate a live feed."
                )
            df = pd.read_csv(csv_path)
            required = {"time", "open", "high", "low", "close"}
            if not required.issubset(set(df.columns)):
                missing = required - set(df.columns)
                raise ValueError(f"CSV missing columns: {sorted(missing)}")
            df = df.sort_values("time")
            return df.tail(int(count)).reset_index(drop=True)

        now = datetime.utcnow()
        times = [now - timedelta(minutes=15 * i) for i in range(count)][::-1]
        base = 1.1
        data = []
        for i, t in enumerate(times):
            drift = 0.0001 * (i - count / 2)
            open_ = base + drift
            close = open_ + 0.0005
            high = max(open_, close) + 0.0002
            low = min(open_, close) - 0.0002
            data.append(
                {
                    "time": t,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                }
            )
        return pd.DataFrame(data)


if __name__ == "__main__":
    fetcher = CandleDataFetcher()
    df = fetcher.fetch_ohlc("EURUSD", count=10, mode="dev")
    print(df.tail())
