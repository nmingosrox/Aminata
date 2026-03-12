from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd

from dataclasses import Signal


class SignalGenerator:
    """
    Combines macro, candle, and tick data into per-instrument signals.
    """

    def generate(
        self,
        macro_df: pd.DataFrame,
        candle_df: pd.DataFrame,
        ticks: List[Dict],
        symbol: str,
    ) -> Dict[str, float]:
        if macro_df is None or macro_df.empty:
            raise ValueError("macro_df must be a non-empty DataFrame")
        if candle_df is None or candle_df.empty:
            raise ValueError("candle_df must be a non-empty DataFrame")
        if not isinstance(ticks, list):
            raise ValueError("ticks must be a list of dicts")
        if not symbol:
            raise ValueError("symbol must be a non-empty string")

        required_macro = {"GDP", "CPI", "UnemploymentRate", "TradeBalance", "instrument"}
        if not required_macro.issubset(set(macro_df.columns)):
            missing = required_macro - set(macro_df.columns)
            raise ValueError(f"macro_df missing columns: {sorted(missing)}")

        required_ohlc = {"open", "high", "low", "close"}
        if not required_ohlc.issubset(set(candle_df.columns)):
            missing = required_ohlc - set(candle_df.columns)
            raise ValueError(f"candle_df missing columns: {sorted(missing)}")

        macro_row = macro_df[macro_df["instrument"] == symbol]
        if macro_row.empty:
            raise ValueError(f"macro_df has no rows for symbol: {symbol}")

        macro_vals = macro_row.iloc[-1]
        macro_score = float(
            (macro_vals["GDP"] - macro_vals["UnemploymentRate"]) * 0.1
            + (macro_vals["CPI"] * 0.05)
            + (macro_vals["TradeBalance"] * 0.1)
        )

        closes = candle_df["close"].astype(float)
        if len(closes) < 10:
            raise ValueError("candle_df must have at least 10 rows")

        fast = closes.rolling(5).mean().iloc[-1]
        slow = closes.rolling(10).mean().iloc[-1]
        tech_score = float((fast - slow) / slow) if slow else 0.0

        tick_score = 0.0
        if ticks:
            last = ticks[-1]
            bid = float(last.get("bid", 0.0))
            ask = float(last.get("ask", 0.0))
            if ask > 0 and bid > 0:
                tick_score = float((ask - bid) / ask)

        blended = 0.5 * macro_score + 0.4 * tech_score - 0.1 * tick_score
        signal = max(-1.0, min(1.0, blended))

        return {symbol: signal}

    def as_dataclass(self, signals: Dict[str, float]) -> List[Signal]:
        if not isinstance(signals, dict):
            raise ValueError("signals must be a dict")
        now = datetime.utcnow()
        return [Signal(instrument=k, strength=float(v), timestamp=now) for k, v in signals.items()]
