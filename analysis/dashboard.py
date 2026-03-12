from __future__ import annotations

import pandas as pd


class Dashboard:
    """
    Summarizes performance and exposure.
    """

    def summarize(self, trades_df: pd.DataFrame) -> str:
        if trades_df is None or trades_df.empty:
            return "Dashboard: No trades to report."
        required = {"pnl", "symbol", "side", "size"}
        if not required.issubset(set(trades_df.columns)):
            missing = required - set(trades_df.columns)
            raise ValueError(f"trades_df missing columns: {sorted(missing)}")

        total_pnl = float(trades_df["pnl"].sum())
        win_rate = float((trades_df["pnl"] > 0).mean())
        exposure = trades_df.groupby("symbol")["size"].sum().to_dict()

        return (
            f"Dashboard: Total PnL={total_pnl:.2f}, "
            f"Win Rate={win_rate:.2%}, Exposure={exposure}"
        )
