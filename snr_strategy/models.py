"""Shared data structures for the SNR strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from .levels import LevelType

Direction = Literal["long", "short"]


@dataclass(slots=True)
class Trade:
    """Represents an executed trade in the backtest."""

    direction: Direction
    entry_index: int
    entry_price: float
    stop_price: float
    target_price: float
    level_type: LevelType
    exit_index: Optional[int] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: float = 0.0

    def close(self, index: int, price: float, reason: str) -> None:
        self.exit_index = index
        self.exit_price = price
        self.exit_reason = reason
        if self.direction == "long":
            self.pnl = price - self.entry_price
        else:
            self.pnl = self.entry_price - price

    @property
    def is_open(self) -> bool:
        return self.exit_index is None

    @property
    def result(self) -> str:
        if self.pnl > 0:
            return "win"
        if self.pnl < 0:
            return "loss"
        return "breakeven"
