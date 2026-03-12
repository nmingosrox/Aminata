from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from dataclasses import Allocation


class PortfolioManager:
    """
    Blends signals into raw allocations.
    """

    def __init__(self, weights: Dict[str, float] | None = None):
        self.weights = weights or {"signal": 1.0}

    def allocate(self, signals: Dict[str, float]) -> Dict[str, float]:
        if not isinstance(signals, dict) or not signals:
            raise ValueError("signals must be a non-empty dict")

        allocations: Dict[str, float] = {}
        weight = float(self.weights.get("signal", 1.0))
        for sym, val in signals.items():
            allocations[sym] = float(val) * weight
        return allocations

    def as_dataclass(self, allocations: Dict[str, float]) -> List[Allocation]:
        if not isinstance(allocations, dict):
            raise ValueError("allocations must be a dict")
        now = datetime.utcnow()
        return [Allocation(instrument=k, weight=float(v), timestamp=now) for k, v in allocations.items()]
