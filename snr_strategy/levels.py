"""SNR detection and management utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import pandas as pd

from .config import StrategyParameters

LevelType = Literal["support", "resistance"]


@dataclass(slots=True)
class SNRLevel:
    """Representation of a detected support or resistance level."""

    level_type: LevelType
    price: float
    confirmation_index: int


class SNRManager:
    """Maintain the most recent support and resistance levels."""

    def __init__(self) -> None:
        self._levels: dict[LevelType, Optional[SNRLevel]] = {"support": None, "resistance": None}

    def update(self, level: SNRLevel) -> None:
        self._levels[level.level_type] = level

    def latest(self, level_type: LevelType) -> Optional[SNRLevel]:
        return self._levels[level_type]

    def invalidate(self, level_type: LevelType) -> None:
        self._levels[level_type] = None


class SNRDetector:
    """Detect stable support and resistance levels."""

    def __init__(self, params: StrategyParameters) -> None:
        self.params = params

    def evaluate(self, df: pd.DataFrame, index: int, avg_prices: pd.Series) -> Optional[SNRLevel]:
        if index <= 0:
            return None

        prev = df.iloc[index - 1]
        curr = df.iloc[index]
        avg_price = avg_prices.iloc[index]
        is_co_match = abs(prev["close"] - curr["open"]) <= avg_price * self.params.co_tolerance_pct

        if not is_co_match:
            return None

        if prev["close"] < prev["open"] and curr["close"] > curr["open"]:
            return SNRLevel("support", price=float(prev["close"]), confirmation_index=index)
        if prev["close"] > prev["open"] and curr["close"] < curr["open"]:
            return SNRLevel("resistance", price=float(prev["close"]), confirmation_index=index)
        return None
