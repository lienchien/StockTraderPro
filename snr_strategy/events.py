"""Event models used for instrumentation of the strategy workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .levels import LevelType, SNRLevel


class StrategyState(str, Enum):
    """Enumerates the major states of the strategy state machine."""

    DETECTION = "detection"
    CONFIRMATION = "confirmation"
    RETEST = "retest"
    TRADE_EXECUTION = "trade_execution"
    EXIT = "exit"


@dataclass(slots=True)
class DetectionEvent:
    """Represents the confirmation of a new support/resistance level."""

    index: int
    level: SNRLevel


@dataclass(slots=True)
class RetestEvent:
    """Captures the evaluation of a retest attempt at a tracked level."""

    index: int
    level_type: LevelType
    price: float
    atr: float
    tolerance: float
    distance: float
    triggered: bool
    reason: str | None


@dataclass(slots=True)
class StateTransition:
    """Records a transition between states for auditability."""

    index: int
    from_state: StrategyState
    to_state: StrategyState


__all__ = [
    "StrategyState",
    "DetectionEvent",
    "RetestEvent",
    "StateTransition",
]

