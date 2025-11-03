"""Performance metrics for the strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

from .config import StrategyParameters
from .models import Trade


@dataclass(slots=True)
class PerformanceMetrics:
    win_rate: float
    profit_factor: float
    max_drawdown: float
    rr_ratio: float
    false_retest_rate: float
    total_trades: int
    net_profit: float


def _max_drawdown(equity_curve: Iterable[float]) -> float:
    peak = -np.inf
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        drawdown = value - peak
        max_dd = min(max_dd, drawdown)
    return abs(max_dd)


def compute_metrics(trades: List[Trade], equity_curve: List[float], params: StrategyParameters) -> PerformanceMetrics:
    if not trades:
        return PerformanceMetrics(0.0, 0.0, 0.0, params.risk_reward_ratio, 0.0, 0, 0.0)

    profits = [trade.pnl for trade in trades]
    wins = sum(1 for trade in trades if trade.pnl > 0)
    losses = [pnl for pnl in profits if pnl < 0]
    gross_profit = sum(pnl for pnl in profits if pnl > 0)
    gross_loss = sum(losses)

    if gross_loss == 0:
        profit_factor = float("inf") if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / abs(gross_loss)

    win_rate = wins / len(trades)
    rr_ratio = float(np.mean([abs(pnl) / params.sl_points for pnl in profits]))
    false_retest_rate = sum(1 for trade in trades if trade.pnl <= 0) / len(trades)
    max_dd = _max_drawdown(equity_curve)
    net_profit = sum(profits)

    return PerformanceMetrics(
        win_rate=win_rate,
        profit_factor=profit_factor,
        max_drawdown=max_dd,
        rr_ratio=rr_ratio,
        false_retest_rate=false_retest_rate,
        total_trades=len(trades),
        net_profit=net_profit,
    )
