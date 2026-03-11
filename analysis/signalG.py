"""
Signal generation module.
"""
from typing import Dict, List, Optional

import numpy as np


class SignalGenerator:
    """
    SignalGenerator combines macro, calendar, and technical data into
    normalized trading signals for each symbol.
    """

    def __init__(self, macro_source=None, candle_source=None, tick_source=None):
        """
        Initializes the SignalGenerator with data sources.

        Args:
            macro_source: Module providing macro and calendar signals.
            candle_source: Module providing OHLC candle data.
            tick_source: Module providing tick data.
        """
        self.macro_source = macro_source
        self.candle_source = candle_source
        self.tick_source = tick_source

    def generate(self, symbols: Optional[List[str]] = [], timeframe: str = "M15", count: int = 200,
                 weights: Optional[Dict[str, float]] = {"macro": 0.4, "calendar": 0.3, "technical": 0.3}) -> Dict[str, Dict[str, float]]:
        """
        Generate signals for the given symbols by combining different sources.
        Each signal component is normalized to a range of -1 to +1.

        Args:
            symbols (list): List of trading symbols (e.g., ["EURUSD"]).
            timeframe (str): Candle timeframe for technical signals.
            count (int): Number of candles for technical calculations.
            weights (dict): Optional weights for blending signals.

        Returns:
            dict: Signals per symbol with macro, calendar, technical, and blended values.
        """

        macro_signals = {}
        calendar_signals = {}
        if self.macro_source is None:
            print("\nMissing source for generating macro signal\n")
            quit()
        
        macro_signals = self.macro_source.get_macro_signals(symbols=symbols)
        calendar_signals = self.macro_source.get_calendar_signals(symbols=symbols)

        signals = {}
        for sym in symbols:
            candles = []
            if self.candle_source is not None:
                candles = self.candle_source.get_candles(sym, timeframe, count)
            technical_signal = self._calculate_technical_signal(candles)

            macro_val = float(macro_signals.get(sym, 0.0))
            calendar_val = float(calendar_signals.get(sym, 0.0))

            blended = (
                weights.get("macro", 0.0) * macro_val
                + weights.get("calendar", 0.0) * calendar_val
                + weights.get("technical", 0.0) * technical_signal
            )
            blended = self._clamp(blended)

            signals[sym] = {
                "macro": self._clamp(macro_val),
                "calendar": self._clamp(calendar_val),
                "technical": self._clamp(technical_signal),
                "blended": blended,
            }
        return signals

    def _calculate_technical_signal(self, candles: List[dict]) -> float:
        """
        Calculate a technical signal using moving averages and RSI.

        Args:
            candles (list): Candle dictionaries with close prices.

        Returns:
            float: Normalized technical signal in [-1, 1].
        """
        if not candles:
            return 0.0
        closes = [c["close"] for c in candles if "close" in c]
        if len(closes) < 20:
            return 0.0

        fast = self._sma(closes, 10)
        slow = self._sma(closes, 30)
        rsi = self._rsi(closes, 14)

        ma_diff = (fast - slow) / slow if slow else 0.0
        ma_score = self._clamp(ma_diff * 5.0)
        rsi_score = self._clamp((rsi - 50.0) / 50.0)

        return self._clamp(0.6 * ma_score + 0.4 * rsi_score)

    def _sma(self, series: List[float], period: int) -> float:
        """
        Compute simple moving average.

        Args:
            series (list): Price series.
            period (int): Lookback period.

        Returns:
            float: SMA value.
        """
        if len(series) < period:
            return float(np.mean(series))
        return float(np.mean(series[-period:]))

    def _rsi(self, series: List[float], period: int) -> float:
        """
        Compute Relative Strength Index.

        Args:
            series (list): Price series.
            period (int): Lookback period.

        Returns:
            float: RSI value between 0 and 100.
        """
        if len(series) < period + 1:
            return 50.0
        deltas = np.diff(series[-(period + 1):])
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _clamp(self, value: float) -> float:
        """
        Clamp a value to [-1, 1].

        Args:
            value (float): Input value.

        Returns:
            float: Clamped value.
        """
        return float(max(-1.0, min(1.0, value)))

    def get_price_series(self, symbol: str, timeframe: str = "M15", count: int = 200) -> List[float]:
        """
        Return recent price series for a symbol, used for volatility calculation.

        Args:
            symbol (str): The trading symbol.
            timeframe (str): Candle timeframe.
            count (int): Number of candles.

        Returns:
            list: Close prices.
        """
        if self.candle_source is None:
            return []
        if hasattr(self.candle_source, "get_close_series"):
            return self.candle_source.get_close_series(symbol, timeframe, count)
        candles = self.candle_source.get_candles(symbol, timeframe, count)
        return [c["close"] for c in candles]

    def get_current_price(self, symbol: str) -> float:
        """
        Return the latest market price for a symbol.

        Args:
            symbol (str): The trading symbol.

        Returns:
            float: Latest price if available, else 0.0.
        """
        if self.tick_source is None:
            return 0.0
        ticks = self.tick_source.get_ticks(symbol, None, 1)
        if ticks:
            return float(ticks[-1].get("last") or ticks[-1].get("bid") or 0.0)
        return 0.0
