"""
Trade logging utilities.
"""
from datetime import datetime
from typing import Optional


class TradeLogger:
    """
    TradeLogger records all trading activities and performance results to a log file.
    """

    def __init__(self, filename: str = "trades.log"):
        """
        Initializes the logger.

        Args:
            filename (str): The name of the file to log trades to.
        """
        self.filename = filename

    def log_trade(self, symbol: str, entry: float, exit: float, pnl: float,
                  timestamp: Optional[str] = None) -> None:
        """
        Record the details of a single trade to the log file.

        Args:
            symbol (str): The trading symbol (e.g., "EURUSD").
            entry (float): Entry price.
            exit (float): Exit price.
            pnl (float): Profit or loss from the trade.
            timestamp (str): Optional ISO timestamp, defaults to current time.

        Returns:
            None
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        line = f"{timestamp},{symbol},{entry},{exit},{pnl}\n"
        header = "timestamp,symbol,entry,exit,pnl\n"
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                if f.tell() == 0:
                    f.write(header)
                f.write(line)
        except FileNotFoundError:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(header)
                f.write(line)
