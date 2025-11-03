# 4H SNR Retest Entry Strategy

## Overview

This project implements the "4H SNR Retest Entry Strategy" described by Zhang Lianrong. The system focuses on detecting stable Support & Resistance (SNR) zones on 4-hour candles, waiting for controlled retests, and executing trades with a fixed risk-reward ratio. The codebase is organized as a lightweight Python package that provides:

- Parameter management for trader-controlled tuning.
- Modular detection of reversal-based SNR levels.
- Retest validation using ATR-driven tolerance bands.
- Trade execution with deterministic stop-loss and take-profit handling.
- Performance analytics aligned with the strategy specification.
- A simple optimization interface for backtesting workflows and automated parameter sweeps.
- Built-in instrumentation for auditing detections, retests, and state transitions.

All components are written in pure Python and use pandas for data handling, making the project easy to integrate with external data feeds or research pipelines.

## Architecture

```
snr_strategy/
├── config.py          # Parameter definitions
├── indicators.py      # Average price & ATR utilities
├── levels.py          # SNR detection and management
├── models.py          # Shared dataclasses (trades, enums)
├── retest.py          # Retest validation logic
├── strategy.py        # End-to-end state machine & backtesting
├── metrics.py         # Performance metric calculations
└── optimization.py    # Grid-search based optimization helper
```

The package exposes the following high-level entry points:

- `StrategyParameters` – dataclass encapsulating the tunable parameters (`sl_points`, `tp_points`, `co_tolerance_pct`, `retest_atr_factor`, `atr_length`).
- `SNRRetestStrategy` – orchestrates the detection, retest validation, trade execution, and metric computation.
- `grid_search` – evaluates multiple parameter combinations according to the optimization objective: `ProfitFactor + α * WinRate - β * MaxDrawdown`.

## Key Concepts

### Candle Stability
The detector verifies that consecutive candles transition smoothly using the formula:

```
abs(previous_close - current_open) <= average_price * co_tolerance_pct
```

Only when this stability holds do we test for reversal structures. Bearish-to-bullish transitions create support levels, while bullish-to-bearish transitions create resistance levels.

### Retest Logic
Once a level is confirmed, the strategy waits for subsequent candles that:

- Touch the level within `ATR * retest_atr_factor`.
- Close back on the "safe" side of the level (above support or below resistance).
- Are different from the confirmation candle.

Valid retests trigger trades with fixed stop-loss and take-profit distances (`sl_points`, `tp_points`).

### Performance Metrics
The `StrategyResult` object captures

- Trade ledger with direction, entry/exit info, and PnL.
- Equity curve aligned with the input data index.
- `PerformanceMetrics` featuring win rate, profit factor, max drawdown, reward/risk ratio, false retest rate, and net profit.
- Recorded `DetectionEvent`, `RetestEvent`, and `StateTransition` sequences for deeper diagnostics.

## Instrumentation & Diagnostics

- `StrategyResult` now provides full visibility into the strategy state machine via `detections`, `retests`, and `state_transitions` collections.
- `RetestDetector.evaluate` returns a `RetestEvaluation` object that explains why a retest passed or failed (e.g., outside tolerance, close breach, confirmation candle).
- These artifacts make it easier to troubleshoot false signals, understand optimization outcomes, and build explainable trading reports.

## Usage Example

```python
import pandas as pd
from snr_strategy import SNRRetestStrategy, StrategyParameters

# Load your 4H OHLC data as a pandas DataFrame with columns: open, high, low, close
prices = pd.read_csv("4h_prices.csv")

params = StrategyParameters(
    sl_points=120,
    tp_points=240,
    co_tolerance_pct=0.002,
    retest_atr_factor=1.0,
    atr_length=14,
)

strategy = SNRRetestStrategy(params)
result = strategy.run(prices)

print(result.metrics)
print(result.trades[0])
```

## Optimization

```python
from snr_strategy.optimization import OptimizationConfig, grid_search

config = OptimizationConfig(
    co_tolerance_values=[0.0015, 0.002, 0.0025],
    retest_atr_values=[0.75, 1.0, 1.25],
    sl_points=[80, 100, 120],
)

ranked_results = grid_search(prices, config)
best = ranked_results[0]
print(best.parameters)
print(best.metrics)
```

The results are returned sorted by the objective value, enabling easy selection of top-performing configurations.

## Development & Testing

1. Install dependencies: `pip install -e .[test]`
2. Run the test suite: `pytest`

Sample datasets for testing are included directly in the unit tests for reproducibility.

## License

This repository is provided for educational and research purposes. Adapt the modules to suit your execution environment or integrate them into larger trading platforms as needed.
