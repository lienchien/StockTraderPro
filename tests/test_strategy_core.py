import math

import pandas as pd

from snr_strategy.config import StrategyParameters
from snr_strategy.indicators import average_price
from snr_strategy.levels import SNRDetector
from snr_strategy.optimization import OptimizationConfig, grid_search
from snr_strategy.strategy import SNRRetestStrategy


def _sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 100.2, "high": 101.3, "low": 98.8, "close": 99.0},
            {"open": 99.05, "high": 101.5, "low": 98.9, "close": 101.4},
            {"open": 101.2, "high": 101.6, "low": 99.1, "close": 100.8},
            {"open": 100.9, "high": 103.5, "low": 100.5, "close": 103.0},
            {"open": 102.5, "high": 103.2, "low": 101.8, "close": 102.0},
        ]
    )


def test_support_detection() -> None:
    data = _sample_data()
    params = StrategyParameters(co_tolerance_pct=0.003, atr_length=3)
    detector = SNRDetector(params)
    avg_prices = average_price(data)

    level = detector.evaluate(data, 2, avg_prices)
    assert level is not None
    assert level.level_type == "support"
    assert math.isclose(level.price, data.iloc[1]["close"], rel_tol=1e-6)

    # Ensure no resistance is detected on same pattern
    assert detector.evaluate(data, 3, avg_prices) is None


def test_strategy_executes_retest_trade() -> None:
    data = _sample_data()
    params = StrategyParameters(
        sl_points=1.0,
        tp_points=2.0,
        co_tolerance_pct=0.003,
        retest_atr_factor=0.5,
        atr_length=3,
    )
    strategy = SNRRetestStrategy(params)
    result = strategy.run(data)

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.direction == "long"
    assert trade.exit_reason == "target"
    assert math.isclose(trade.pnl, 2.0, rel_tol=1e-6)

    metrics = result.metrics
    assert metrics.win_rate == 1.0
    assert math.isinf(metrics.profit_factor)
    assert metrics.false_retest_rate == 0.0
    assert math.isclose(metrics.rr_ratio, 2.0, rel_tol=1e-6)


def test_grid_search_orders_results() -> None:
    data = _sample_data()
    config = OptimizationConfig(
        co_tolerance_values=[0.002, 0.003],
        retest_atr_values=[0.5, 1.0],
        sl_points=[1.0],
        atr_lengths=[3],
    )
    results = grid_search(data, config)
    assert results, "Expected optimization to return results"
    # First result should have objective no smaller than the last
    assert results[0].objective_value >= results[-1].objective_value
