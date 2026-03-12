from __future__ import annotations

from typing import Dict, List

import pandas as pd

from dataclasses import TradeLog


class TradeLogger:
    """
    Records trades and exposes them as a DataFrame.
    """

    def __init__(self):
        self._trades: List[TradeLog] = []

    def record(self, trades: List[TradeLog]) -> pd.DataFrame:
        if not isinstance(trades, list):
            raise ValueError("trades must be a list of TradeLog")
        for t in trades:
            if not isinstance(t, TradeLog):
                raise ValueError("trades must contain TradeLog instances")
        self._trades.extend(trades)
        return self.to_frame()

    def to_frame(self) -> pd.DataFrame:
        if not self._trades:
            return pd.DataFrame(columns=["symbol", "side", "size", "price", "pnl", "timestamp"])
        rows = [
            {
                "symbol": t.symbol,
                "side": t.side,
                "size": t.size,
                "price": t.price,
                "pnl": t.pnl,
                "timestamp": t.timestamp,
            }
            for t in self._trades
        ]
        return pd.DataFrame(rows)

    def exposures(self) -> Dict[str, float]:
        df = self.to_frame()
        if df.empty:
            return {}
        signed = df["size"].where(df["side"] == "buy", -df["size"])
        return dict(df.groupby("symbol")["size"].sum())
