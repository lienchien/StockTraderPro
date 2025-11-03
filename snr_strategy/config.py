"""Parameter definitions for the 4H SNR Retest Entry Strategy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StrategyParameters:
    """Container for user configurable strategy parameters."""

    sl_points: float = 100.0
    tp_points: float = 200.0
    co_tolerance_pct: float = 0.002
    retest_atr_factor: float = 1.0
    atr_length: int = 14

    def __post_init__(self) -> None:
        if self.sl_points <= 0:
            raise ValueError("Stop loss distance must be positive")
        if self.tp_points <= 0:
            raise ValueError("Take profit distance must be positive")
        if not (0 < self.co_tolerance_pct < 0.05):
            raise ValueError("Candle open/close tolerance must be between 0 and 0.05")
        if self.retest_atr_factor <= 0:
            raise ValueError("ATR retest factor must be positive")
        if self.atr_length <= 1:
            raise ValueError("ATR length must be greater than 1")

    @property
    def risk_reward_ratio(self) -> float:
        """Return the configured risk to reward ratio."""

        return self.tp_points / self.sl_points
