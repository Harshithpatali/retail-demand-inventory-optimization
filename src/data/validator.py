"""Validation utilities for the M5 input data."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


SALES_META = [
    "id",
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
]

REQUIRED = {
    "sales_train": SALES_META,
    "calendar": [
        "date",
        "wm_yr_wk",
        "d",
        "weekday",
        "wday",
        "month",
        "year",
    ],
    "prices": [
        "store_id",
        "item_id",
        "wm_yr_wk",
        "sell_price",
    ],
}


def validate_raw_files(raw: Path) -> list[str]:
    """Return required raw files that are missing."""
    required = [
        "sales_train_evaluation.csv",
        "sales_train_validation.csv",
        "calendar.csv",
        "sell_prices.csv",
        "sample_submission.csv",
    ]
    return [name for name in required if not (raw / name).exists()]


def validate_sales_columns(columns: Iterable[str] | pd.DataFrame) -> None:
    """Validate the metadata columns in a sales table or column index.

    Accepting both a DataFrame and an iterable of column names prevents the
    header-only loader path from accidentally treating an Index like a DataFrame.
    """
    if isinstance(columns, pd.DataFrame):
        available = set(columns.columns)
    else:
        available = set(columns)

    missing = [c for c in SALES_META if c not in available]
    if missing:
        raise ValueError(
            f"Sales file missing required columns: {missing}"
        )


def build_validation_report(
    raw: Path,
    selected_sales: pd.DataFrame,
    calendar: pd.DataFrame,
    prices: pd.DataFrame,
) -> dict:
    """Build a compact validation report for the selected data."""
    return {
        "selected_sales_rows": int(len(selected_sales)),
        "selected_series": int(selected_sales["id"].nunique()),
        "calendar_rows": int(len(calendar)),
        "calendar_missing_dates": int(calendar["date"].isna().sum()),
        "price_rows": int(len(prices)),
        "price_missing_sell_price": int(prices["sell_price"].isna().sum()),
        "duplicate_series": int(selected_sales["id"].duplicated().sum()),
    }
