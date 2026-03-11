"""
Performance dashboard utilities.
"""
from typing import List, Dict
import numpy as np


class Dashboard:
    """
    Dashboard calculates and displays key performance indicators (KPIs).
    """

    def __init__(self):
        """
        Initializes the Dashboard module.
        """
        pass

    def update(self, trades: List[Dict]) -> None:
        """
        Update the dashboard with the latest trade data and performance metrics.

        Args:
            trades (list): A list of completed trade dictionaries with pnl or entry/exit.

        Returns:
            None
        """
        if not trades:
            print("Dashboard: No trades to report yet.")
            return

        pnls = []
        for t in trades:
            if "pnl" in t:
                pnls.append(float(t["pnl"]))
            elif "entry" in t and "exit" in t and "size" in t:
                pnls.append((float(t["exit"]) - float(t["entry"])) * float(t["size"]))

        if not pnls:
            print("Dashboard: No valid trade PnL data.")
            return

        total_pnl = float(np.sum(pnls))
        returns = np.array(pnls)
        sharpe = 0.0
        if np.std(returns) > 0:
            sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(len(returns)))

        equity = np.cumsum(returns)
        peak = np.maximum.accumulate(equity)
        drawdowns = (peak - equity)
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) else 0.0

        print(f"Dashboard: Total PnL={total_pnl:.2f}, Sharpe={sharpe:.2f}, Max Drawdown={max_drawdown:.2f}")
