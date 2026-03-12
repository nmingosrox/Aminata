from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Signal:
    instrument: str
    strength: float
    timestamp: datetime


@dataclass(frozen=True)
class Allocation:
    instrument: str
    weight: float
    timestamp: datetime


@dataclass(frozen=True)
class Order:
    symbol: str
    side: str  # "buy" or "sell"
    size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]


@dataclass(frozen=True)
class TradeLog:
    symbol: str
    side: str
    size: float
    price: float
    pnl: float
    timestamp: datetime
