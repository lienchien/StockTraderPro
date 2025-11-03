"""Retest detection logic."""

from __future__ import annotations

import math
from typing import Optional

import pandas as pd

from .config import StrategyParameters
from .levels import LevelType, SNRLevel


class RetestDetector:
    """Detect valid retests of confirmed SNR levels."""

    def __init__(self, params: StrategyParameters) -> None:
        self.params = params
        self._last_signal_index: dict[LevelType, Optional[int]] = {"support": None, "resistance": None}

    def is_valid(self, level: SNRLevel, row: pd.Series, atr_value: float, index: int) -> bool:
        if math.isnan(atr_value):
            return False
        if index == level.confirmation_index:
            return False

        tolerance = atr_value * self.params.retest_atr_factor
        if level.level_type == "support":
            low = float(row["low"])
            close = float(row["close"])
            if close <= level.price:
                return False
            if not (level.price - tolerance <= low <= level.price + tolerance):
                return False
        else:
            high = float(row["high"])
            close = float(row["close"])
            if close >= level.price:
                return False
            if not (level.price - tolerance <= high <= level.price + tolerance):
                return False

        last_index = self._last_signal_index[level.level_type]
        if last_index is not None and index == last_index:
            return False

        self._last_signal_index[level.level_type] = index
        return True

    def invalidate(self, level_type: LevelType) -> None:
        self._last_signal_index[level_type] = None
