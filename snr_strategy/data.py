"""Data preparation utilities for the SNR strategy."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS = ("open", "high", "low", "close")


def _normalize_columns(columns: Iterable[str]) -> list[str]:
    return [str(col).lower() for col in columns]


def prepare_price_data(data: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize OHLC price data.

    The strategy assumes that input data:
      * contains the required OHLC columns (case insensitive)
      * is indexed in chronological order without duplicate timestamps
      * stores numeric values that can be safely cast to float

    This helper enforces those guarantees up front to keep the core
    strategy logic focused on trading rules instead of defensive checks.
    """

    if not isinstance(data, pd.DataFrame):  # pragma: no cover - defensive
        raise TypeError("Price data must be provided as a pandas DataFrame")
    if data.empty:
        raise ValueError("Price data cannot be empty")

    df = data.copy()
    df.columns = _normalize_columns(df.columns)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise KeyError(f"Input data is missing required columns: {missing}")

    df = df.sort_index()
    if df.index.duplicated().any():
        df = df[~df.index.duplicated(keep="last")]  # keep the most recent observation

    numeric = df.loc[:, REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if numeric.isnull().any().any():
        raise ValueError("Price columns must contain numeric values")

    df.loc[:, REQUIRED_COLUMNS] = numeric.astype(float)
    df.attrs["snr_prepared"] = True
    return df


__all__ = ["prepare_price_data"]
