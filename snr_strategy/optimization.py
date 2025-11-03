"""Parameter optimization helpers for the SNR strategy."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import List, Sequence

import pandas as pd

from .config import StrategyParameters
from .data import prepare_price_data
from .metrics import PerformanceMetrics
from .strategy import SNRRetestStrategy, StrategyResult


@dataclass(slots=True)
class OptimizationConfig:
    co_tolerance_values: Sequence[float]
    retest_atr_values: Sequence[float]
    sl_points: Sequence[float]
    atr_lengths: Sequence[int] = (14,)
    alpha: float = 0.3
    beta: float = 0.5


@dataclass(slots=True)
class OptimizationResult:
    parameters: StrategyParameters
    metrics: PerformanceMetrics
    objective_value: float


def grid_search(data: pd.DataFrame, config: OptimizationConfig) -> List[OptimizationResult]:
    """Evaluate parameter combinations and return ranked results."""

    prepared_data = prepare_price_data(data)
    results: List[OptimizationResult] = []
    for co_tol, atr_factor, sl_points, atr_length in product(
        config.co_tolerance_values,
        config.retest_atr_values,
        config.sl_points,
        config.atr_lengths,
    ):
        params = StrategyParameters(
            sl_points=sl_points,
            tp_points=sl_points * 2,
            co_tolerance_pct=co_tol,
            retest_atr_factor=atr_factor,
            atr_length=atr_length,
        )
        strategy = SNRRetestStrategy(params)
        result: StrategyResult = strategy.run(prepared_data)
        objective = _objective_value(result.metrics, config)
        results.append(
            OptimizationResult(
                parameters=params,
                metrics=result.metrics,
                objective_value=objective,
            )
        )

    results.sort(key=lambda item: item.objective_value, reverse=True)
    return results


def _objective_value(metrics: PerformanceMetrics, config: OptimizationConfig) -> float:
    return metrics.profit_factor + config.alpha * metrics.win_rate - config.beta * metrics.max_drawdown
