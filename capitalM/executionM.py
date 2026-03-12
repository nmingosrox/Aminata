from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from dataclasses import Order, TradeLog


class ExecutionManager:
    """
    Converts risk-adjusted allocations into orders and simulated trades.
    """

    def __init__(self, mode: str = "dev"):
        if mode not in {"dev", "prod"}:
            raise ValueError("mode must be 'dev' or 'prod'")
        self.mode = mode

    def create_orders(
        self,
        allocations: Dict[str, float],
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> List[Order]:
        if not isinstance(allocations, dict) or not allocations:
            raise ValueError("allocations must be a non-empty dict")

        orders: List[Order] = []
        for sym, weight in allocations.items():
            size = abs(float(weight))
            if size == 0:
                continue
            side = "buy" if weight > 0 else "sell"
            orders.append(
                Order(
                    symbol=sym,
                    side=side,
                    size=size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
            )
        return orders

    def execute(self, orders: List[Order]) -> List[TradeLog]:
        if not isinstance(orders, list):
            raise ValueError("orders must be a list of Order")
        if self.mode == "prod":
            raise NotImplementedError(
                "Live execution not configured. Integrate broker API here."
            )

        trades: List[TradeLog] = []
        now = datetime.utcnow()
        for o in orders:
            price = 1.0  # placeholder simulated fill
            pnl = 0.0
            trades.append(
                TradeLog(
                    symbol=o.symbol,
                    side=o.side,
                    size=o.size,
                    price=price,
                    pnl=pnl,
                    timestamp=now,
                )
            )
        return trades
