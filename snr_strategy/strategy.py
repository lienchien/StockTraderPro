"""End-to-end implementation of the 4H SNR Retest Entry Strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import pandas as pd

from .config import StrategyParameters
from .events import DetectionEvent, RetestEvent, StateTransition, StrategyState
from .indicators import atr, average_price
from .levels import SNRDetector, SNRLevel, SNRManager
from .metrics import PerformanceMetrics, compute_metrics
from .models import Direction, Trade
from .retest import RetestDetector, RetestEvaluation


@dataclass(slots=True)
class StrategyResult:
    """Container for the results of a strategy run."""

    trades: List[Trade]
    equity_curve: pd.Series
    metrics: PerformanceMetrics
    detections: List[DetectionEvent]
    retests: List[RetestEvent]
    state_transitions: List[StateTransition]


class SNRRetestStrategy:
    """Implements the state machine described in the strategy specification."""

    def __init__(self, params: Optional[StrategyParameters] = None) -> None:
        self.params = params or StrategyParameters()

    def run(self, data: pd.DataFrame) -> StrategyResult:
        df = data.copy()
        df = df.rename(columns=str.lower)
        required = {"open", "high", "low", "close"}
        if missing := required.difference(df.columns):
            raise KeyError(f"Input data is missing required columns: {sorted(missing)}")

        avg_prices = average_price(df)
        atr_values = atr(df, self.params.atr_length)

        detector = SNRDetector(self.params)
        manager = SNRManager()
        retest_detector = RetestDetector(self.params)

        trades: List[Trade] = []
        equity_curve: List[float] = []
        detections: List[DetectionEvent] = []
        retest_events: List[RetestEvent] = []
        state_transitions: List[StateTransition] = []
        state = StrategyState.DETECTION

        def transition(new_state: StrategyState, idx: int) -> None:
            nonlocal state
            if new_state != state:
                state_transitions.append(StateTransition(index=idx, from_state=state, to_state=new_state))
                state = new_state

        equity = 0.0
        open_trade: Optional[Trade] = None

        for index in range(len(df)):
            row = df.iloc[index]
            atr_value = float(atr_values.iloc[index]) if index < len(atr_values) else float("nan")

            level = detector.evaluate(df, index, avg_prices)
            if level:
                detections.append(DetectionEvent(index=index, level=level))
                transition(StrategyState.CONFIRMATION, index)
                manager.update(level)
                retest_detector.invalidate(level.level_type)

            if open_trade is None and manager.has_active_levels():
                transition(StrategyState.RETEST, index)

            # invalidate levels that are breached by closes
            support = manager.latest("support")
            if support and float(row["close"]) < support.price:
                manager.invalidate("support")
                retest_detector.invalidate("support")
                if open_trade is None and not manager.has_active_levels():
                    transition(StrategyState.DETECTION, index)

            resistance = manager.latest("resistance")
            if resistance and float(row["close"]) > resistance.price:
                manager.invalidate("resistance")
                retest_detector.invalidate("resistance")
                if open_trade is None and not manager.has_active_levels():
                    transition(StrategyState.DETECTION, index)

            if open_trade is not None:
                self._evaluate_exit(open_trade, row, index)
                if not open_trade.is_open:
                    trades.append(open_trade)
                    equity += open_trade.pnl
                    transition(StrategyState.EXIT, index)
                    open_trade = None
                    transition(StrategyState.DETECTION, index)

            if open_trade is None and manager.has_active_levels():
                for direction, level, evaluation in self._evaluate_retests(
                    manager, retest_detector, row, atr_value, index
                ):
                    retest_events.append(
                        RetestEvent(
                            index=index,
                            level_type=level.level_type,
                            price=float(row["close"]),
                            atr=atr_value,
                            tolerance=evaluation.tolerance,
                            distance=evaluation.distance,
                            triggered=evaluation.is_valid,
                            reason=evaluation.reason,
                        )
                    )
                    if evaluation.is_valid:
                        open_trade = self._open_trade(
                            direction, level, row, manager, retest_detector, index
                        )
                        transition(StrategyState.TRADE_EXECUTION, index)
                        break

                if open_trade is None and not manager.has_active_levels():
                    transition(StrategyState.DETECTION, index)

            equity_curve.append(equity)

        if open_trade is not None:
            final_index = len(df) - 1
            final_price = float(df.iloc[-1]["close"])
            open_trade.close(final_index, final_price, "close")
            trades.append(open_trade)
            equity += open_trade.pnl
            transition(StrategyState.EXIT, final_index)
            open_trade = None
            transition(StrategyState.DETECTION, final_index)
            if equity_curve:
                equity_curve[-1] = equity
            else:
                equity_curve.append(equity)

        if state != StrategyState.DETECTION and len(df):
            transition(StrategyState.DETECTION, len(df) - 1)

        equity_series = pd.Series(equity_curve, index=df.index)
        metrics = compute_metrics(trades, equity_curve, self.params)
        return StrategyResult(
            trades=trades,
            equity_curve=equity_series,
            metrics=metrics,
            detections=detections,
            retests=retest_events,
            state_transitions=state_transitions,
        )

    def _evaluate_exit(self, trade: Trade, row: pd.Series, index: int) -> None:
        if trade.direction == "long":
            if float(row["low"]) <= trade.stop_price:
                trade.close(index, trade.stop_price, "stop")
            elif float(row["high"]) >= trade.target_price:
                trade.close(index, trade.target_price, "target")
        else:
            if float(row["high"]) >= trade.stop_price:
                trade.close(index, trade.stop_price, "stop")
            elif float(row["low"]) <= trade.target_price:
                trade.close(index, trade.target_price, "target")

    def _evaluate_retests(
        self,
        manager: SNRManager,
        retest_detector: RetestDetector,
        row: pd.Series,
        atr_value: float,
        index: int,
    ) -> Sequence[Tuple[Direction, SNRLevel, RetestEvaluation]]:
        candidates: list[Tuple[Direction, SNRLevel, RetestEvaluation]] = []
        support = manager.latest("support")
        if support is not None:
            evaluation = retest_detector.evaluate(support, row, atr_value, index)
            candidates.append(("long", support, evaluation))
            if evaluation.is_valid:
                return candidates

        resistance = manager.latest("resistance")
        if resistance is not None:
            evaluation = retest_detector.evaluate(resistance, row, atr_value, index)
            candidates.append(("short", resistance, evaluation))

        return candidates

    def _open_trade(
        self,
        direction: Direction,
        level,
        row: pd.Series,
        manager: SNRManager,
        retest_detector: RetestDetector,
        index: int,
    ) -> Trade:
        close_price = float(row["close"])
        if direction == "long":
            stop_price = close_price - self.params.sl_points
            target_price = close_price + self.params.tp_points
        else:
            stop_price = close_price + self.params.sl_points
            target_price = close_price - self.params.tp_points

        trade = Trade(
            direction=direction,
            entry_index=index,
            entry_price=close_price,
            stop_price=stop_price,
            target_price=target_price,
            level_type=level.level_type,
        )
        manager.invalidate(level.level_type)
        retest_detector.invalidate(level.level_type)
        return trade
