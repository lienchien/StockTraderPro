"""Indicator utilities for the SNR strategy."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = ("open", "high", "low", "close")


def _assert_columns(df: pd.DataFrame) -> None:
    columns = {col.lower() for col in df.columns}
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        raise KeyError(f"DataFrame is missing columns: {missing}")


def average_price(df: pd.DataFrame) -> pd.Series:
    """Return the typical price used for stability checks."""

    _assert_columns(df)
    return (df["high"] + df["low"] + df["close"]) / 3


def atr(df: pd.DataFrame, period: int) -> pd.Series:
    """Compute the Average True Range."""

    if period <= 1:
        raise ValueError("ATR period must be greater than 1")
    _assert_columns(df)

    highs = df["high"].astype(float)
    lows = df["low"].astype(float)
    closes = df["close"].astype(float)

    prev_close = closes.shift(1)
    high_low = highs - lows
    high_close = (highs - prev_close).abs()
    low_close = (lows - prev_close).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period, min_periods=period).mean()
