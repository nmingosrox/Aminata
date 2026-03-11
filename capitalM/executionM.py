"""
Execution manager for backtesting and live trading.
"""
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - handled at runtime
    mt5 = None


class ExecutionManager:
    """
    ExecutionManager handles broker connectivity and trade execution.
    It supports backtesting simulation and live MT5 order placement.
    """

    def __init__(self, mode: str = "backtest", price_source: Optional[Callable[[str, str], float]] = None):
        """
        Initialize the ExecutionManager.

        Args:
            mode (str): "backtest" or "live".
            price_source (callable): Optional callable to fetch prices in backtests.
        """
        self.mode = mode
        self.price_source = price_source
        self.connected = False
        self.positions = {}
        self.open_trades = []
        self.closed_trades = []

    def connect(self, login: Optional[int] = None, password: Optional[str] = None,
                server: Optional[str] = None, path: Optional[str] = None) -> bool:
        """
        Connect to the MetaTrader 5 terminal.

        Args:
            login (int): Optional account login.
            password (str): Optional account password.
            server (str): Optional broker server.
            path (str): Optional terminal path.

        Returns:
            bool: True if connected successfully.
        """
        if self.mode == "live":
            if mt5 is None:
                raise RuntimeError("MetaTrader5 package is not installed.")
            self.connected = mt5.initialize(path=path, login=login, password=password, server=server)
        else:
            self.connected = True
        return self.connected

    def rebalance(self, allocations: Dict[str, float], fill_mode: str = "next_open") -> List[Dict[str, Any]]:
        """
        Execute trades to adjust positions to match target allocations.

        Args:
            allocations (dict): Target position sizes per symbol (units).
            fill_mode (str): "next_open" or "tick" for backtest fills.

        Returns:
            list: Executed trade records.
        """
        executed = []
        for symbol, target_size in allocations.items():
            current_size = float(self.positions.get(symbol, 0.0))
            delta = float(target_size) - current_size
            if abs(delta) < 1e-8:
                continue

            if self.mode == "live":
                trade = self._send_order(symbol, delta)
            else:
                price = self._get_backtest_price(symbol, fill_mode)
                if price is None:
                    continue
                trade = self._simulate_fill(symbol, delta, price)

            if trade:
                executed.append(trade)
        return executed

    def _get_backtest_price(self, symbol: str, fill_mode: str) -> Optional[float]:
        """
        Resolve a backtest fill price using the price source.

        Args:
            symbol (str): The trading symbol.
            fill_mode (str): "next_open" or "tick".

        Returns:
            float: Price if available, else None.
        """
        if self.price_source is None:
            return None
        return float(self.price_source(symbol, fill_mode))

    def _simulate_fill(self, symbol: str, size: float, price: float,
                       tp: Optional[float] = None, sl: Optional[float] = None) -> Dict[str, Any]:
        """
        Simulate a trade fill in backtesting mode.

        Args:
            symbol (str): The trading symbol.
            size (float): Position size delta.
            price (float): Fill price.
            tp (float): Optional take-profit level.
            sl (float): Optional stop-loss level.

        Returns:
            dict: Trade record.
        """
        trade = {
            "symbol": symbol,
            "size": float(size),
            "price": float(price),
            "timestamp": datetime.utcnow().isoformat(),
            "tp": tp,
            "sl": sl,
        }
        self.positions[symbol] = float(self.positions.get(symbol, 0.0)) + float(size)
        self.open_trades.append(trade)
        return trade

    def _send_order(self, symbol: str, size: float) -> Dict[str, Any]:
        """
        Send a market order to MT5 in live mode.

        Args:
            symbol (str): The trading symbol.
            size (float): Position size delta.

        Returns:
            dict: Trade record.
        """
        if mt5 is None:
            raise RuntimeError("MetaTrader5 package is not installed.")
        if not self.connected:
            raise RuntimeError("ExecutionManager is not connected.")

        action = mt5.TRADE_ACTION_DEAL
        order_type = mt5.ORDER_TYPE_BUY if size > 0 else mt5.ORDER_TYPE_SELL
        volume = abs(float(size))
        price = mt5.symbol_info_tick(symbol).ask if size > 0 else mt5.symbol_info_tick(symbol).bid

        request = {
            "action": action,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 10,
            "magic": 10001,
            "comment": "auto-trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        trade = {
            "symbol": symbol,
            "size": float(size),
            "price": float(price),
            "timestamp": datetime.utcnow().isoformat(),
            "result": result,
        }
        self.positions[symbol] = float(self.positions.get(symbol, 0.0)) + float(size)
        self.open_trades.append(trade)
        return trade

    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Monitor open trades and close those that hit TP or SL.

        Args:
            current_prices (dict): Mapping of symbol to latest price.

        Returns:
            list: Closed trade records.
        """
        closed = []
        still_open = []
        for trade in self.open_trades:
            symbol = trade["symbol"]
            price = current_prices.get(symbol)
            if price is None:
                still_open.append(trade)
                continue

            tp = trade.get("tp")
            sl = trade.get("sl")
            size = trade["size"]
            hit_tp = tp is not None and ((price >= tp and size > 0) or (price <= tp and size < 0))
            hit_sl = sl is not None and ((price <= sl and size > 0) or (price >= sl and size < 0))
            if hit_tp or hit_sl:
                close_trade = {
                    "symbol": symbol,
                    "entry": trade["price"],
                    "exit": float(price),
                    "size": size,
                    "timestamp": datetime.utcnow().isoformat(),
                    "pnl": (float(price) - float(trade["price"])) * float(size),
                }
                self.positions[symbol] = float(self.positions.get(symbol, 0.0)) - float(size)
                closed.append(close_trade)
                self.closed_trades.append(close_trade)
            else:
                still_open.append(trade)
        self.open_trades = still_open
        return closed

    def shutdown(self) -> None:
        """
        Disconnect from the MetaTrader 5 terminal.
        """
        if self.mode == "live" and mt5 is not None:
            mt5.shutdown()
        self.connected = False
