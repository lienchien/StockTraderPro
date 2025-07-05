import pandas as pd
import numpy as np
import pytest

from technical_analysis import TechnicalAnalysis


def test_moving_average_basic():
    data = pd.DataFrame({'Close': [1, 2, 3, 4, 5]})
    ta = TechnicalAnalysis(data)
    result = ta.moving_average(3)
    expected = pd.Series([np.nan, np.nan, 2.0, 3.0, 4.0])
    pd.testing.assert_series_equal(result.reset_index(drop=True), expected)


def test_rsi_calculation():
    close_prices = [1, 2, 1, 2, 1]
    data = pd.DataFrame({'Close': close_prices})
    ta = TechnicalAnalysis(data)
    result = ta.rsi(period=2)

    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=2).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=2).mean()
    rs = gain / loss
    expected = 100 - (100 / (1 + rs))

    pd.testing.assert_series_equal(result.reset_index(drop=True), expected.reset_index(drop=True))
