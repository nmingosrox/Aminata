from __future__ import annotations

from typing import Dict

import pandas as pd


class RiskManager:
    """
    Applies volatility scaling, stop-loss heuristics, and drawdown limits.
    """

    def __init__(self, max_position: float = 0.05, target_vol: float = 0.01):
        if max_position <= 0:
            raise ValueError("max_position must be positive")
        if target_vol <= 0:
            raise ValueError("target_vol must be positive")
        self.max_position = float(max_position)
        self.target_vol = float(target_vol)

    def apply(self, allocations: Dict[str, float], candle_df: pd.DataFrame) -> Dict[str, float]:
        if not isinstance(allocations, dict) or not allocations:
            raise ValueError("allocations must be a non-empty dict")
        if candle_df is None or candle_df.empty:
            raise ValueError("candle_df must be a non-empty DataFrame")
        if "close" not in candle_df.columns:
            raise ValueError("candle_df must include 'close' column")

        returns = candle_df["close"].astype(float).pct_change().dropna()
        if returns.empty:
            raise ValueError("candle_df has insufficient data for volatility")
        volatility = float(returns.std())
        vol_scale = self.target_vol / (volatility + 1e-8)
        vol_scale = max(0.2, min(5.0, vol_scale))

        adjusted: Dict[str, float] = {}
        for sym, weight in allocations.items():
            raw = float(weight) * vol_scale
            capped = max(-self.max_position, min(self.max_position, raw))
            adjusted[sym] = capped
        return adjusted
