"""Retest detection logic."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .config import StrategyParameters
from .levels import LevelType, SNRLevel


@dataclass(slots=True)
class RetestEvaluation:
    """Detailed outcome of a retest evaluation."""

    is_valid: bool
    tolerance: float
    distance: float
    reason: Optional[str] = None

    def __bool__(self) -> bool:  # pragma: no cover - convenience wrapper
        return self.is_valid


class RetestDetector:
    """Detect valid retests of confirmed SNR levels."""

    def __init__(self, params: StrategyParameters) -> None:
        self.params = params
        self._last_signal_index: dict[LevelType, Optional[int]] = {"support": None, "resistance": None}

    def evaluate(self, level: SNRLevel, row: pd.Series, atr_value: float, index: int) -> RetestEvaluation:
        if math.isnan(atr_value):
            return RetestEvaluation(False, 0.0, float("nan"), "atr_not_ready")
        if index == level.confirmation_index:
            return RetestEvaluation(False, 0.0, float("nan"), "confirmation_candle")

        tolerance = atr_value * self.params.retest_atr_factor

        if level.level_type == "support":
            low = float(row["low"])
            close = float(row["close"])
            distance = abs(low - level.price)
            if close <= level.price:
                return RetestEvaluation(False, tolerance, distance, "close_below_support")
            if not (level.price - tolerance <= low <= level.price + tolerance):
                return RetestEvaluation(False, tolerance, distance, "outside_tolerance")
        else:
            high = float(row["high"])
            close = float(row["close"])
            distance = abs(high - level.price)
            if close >= level.price:
                return RetestEvaluation(False, tolerance, distance, "close_above_resistance")
            if not (level.price - tolerance <= high <= level.price + tolerance):
                return RetestEvaluation(False, tolerance, distance, "outside_tolerance")

        last_index = self._last_signal_index[level.level_type]
        if last_index is not None and index == last_index:
            return RetestEvaluation(False, tolerance, distance, "duplicate_signal")

        self._last_signal_index[level.level_type] = index
        return RetestEvaluation(True, tolerance, distance, None)

    def is_valid(self, level: SNRLevel, row: pd.Series, atr_value: float, index: int) -> bool:
        """Backward compatible boolean check for legacy callers."""

        return self.evaluate(level, row, atr_value, index).is_valid

    def invalidate(self, level_type: LevelType) -> None:
        self._last_signal_index[level_type] = None
