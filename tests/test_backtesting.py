import pandas as pd
import numpy as np

from backtesting import BacktestEngine


def test_calculate_metrics_simple():
    engine = BacktestEngine()
    portfolio_values = pd.Series([100, 110, 105, 115, 120])
    metrics = engine._calculate_metrics(100, 120, portfolio_values, [])

    total_return_expected = 20.0
    days = len(portfolio_values)
    years = days / 252
    annual_return_expected = ((120 / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
    peak = portfolio_values.expanding().max()
    drawdown = (portfolio_values - peak) / peak * 100
    max_drawdown_expected = drawdown.min()
    returns = portfolio_values.pct_change().dropna()
    excess_returns = returns - (0.02 / 252)
    sharpe_ratio_expected = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() != 0 else 0
    volatility_expected = returns.std() * np.sqrt(252) * 100

    assert np.isclose(metrics['total_return'], total_return_expected)
    assert np.isclose(metrics['annual_return'], annual_return_expected)
    assert np.isclose(metrics['max_drawdown'], max_drawdown_expected)
    assert np.isclose(metrics['sharpe_ratio'], sharpe_ratio_expected)
    assert np.isclose(metrics['volatility'], volatility_expected)
    assert metrics['num_trades'] == 0
