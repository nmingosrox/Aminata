"""
Risk management module.
"""
import numpy as np
from typing import List


class RiskManager:
    """
    RiskManager ensures that all trading decisions adhere to predefined risk
    parameters. It handles position sizing based on volatility, enforces
    max position limits, and monitors portfolio-level drawdown.
    """

    def __init__(self, max_drawdown: float = 0.2, max_position: float = 0.05, target_vol: float = 0.01):
        """
        Initializes the RiskManager with risk parameters.

        Args:
            max_drawdown (float): The maximum allowed portfolio drawdown (e.g., 0.2 for 20%).
            max_position (float): The maximum fraction of capital for a single position.
            target_vol (float): Target volatility used for scaling position sizes.
        """
        self.max_drawdown = float(max_drawdown)
        self.max_position = float(max_position)
        self.target_vol = float(target_vol)
        self.peak_value = None
        self.last_drawdown = 0.0

    def position_size(self, symbol: str, conviction: float, capital: float, price_series: List[float]) -> float:
        """
        Calculate a safe position size based on conviction, volatility, and capital.

        Args:
            symbol (str): The trading symbol.
            conviction (float): The blended signal score (-1 to +1).
            capital (float): Total portfolio capital.
            price_series (list): Recent prices for volatility calculation.

        Returns:
            float: The calculated position size (units). Can be negative for shorts.
        """
        if not price_series:
            return 0.0
        last_price = float(price_series[-1])
        if last_price <= 0:
            return 0.0

        returns = np.diff(price_series) / np.array(price_series[:-1])
        if len(returns) == 0:
            return 0.0
        volatility = float(np.std(returns))
        vol_scale = self.target_vol / (volatility + 1e-8)
        vol_scale = min(max(vol_scale, 0.2), 5.0)

        max_notional = capital * self.max_position
        desired_notional = capital * self.max_position * float(conviction) * vol_scale
        capped_notional = max(-max_notional, min(max_notional, desired_notional))

        return capped_notional / last_price

    def update_drawdown(self, portfolio_value: float) -> float:
        """
        Update peak portfolio value and compute current drawdown.

        Args:
            portfolio_value (float): Current portfolio value.

        Returns:
            float: Current drawdown as a fraction.
        """
        if self.peak_value is None:
            self.peak_value = portfolio_value
        self.peak_value = max(self.peak_value, portfolio_value)
        if self.peak_value <= 0:
            self.last_drawdown = 0.0
        else:
            self.last_drawdown = (self.peak_value - portfolio_value) / self.peak_value
        return self.last_drawdown

    def check_drawdown(self, portfolio_value: float) -> bool:
        """
        Check if the current portfolio drawdown exceeds the maximum allowed limit.

        Args:
            portfolio_value (float): Current portfolio value.

        Returns:
            bool: True if drawdown exceeds the limit.
        """
        drawdown = self.update_drawdown(portfolio_value)
        return drawdown > self.max_drawdown
