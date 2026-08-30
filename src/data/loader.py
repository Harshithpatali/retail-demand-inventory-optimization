"""Memory-conscious M5 data loading and deterministic high-demand selection."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.validator import validate_raw_files, validate_sales_columns


REQUIRED_META_COLUMNS = [
    "id",
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
]


def raw_paths(root: Path) -> dict[str, Path]:
    """Return canonical raw-data paths."""
    return {
        "evaluation": root / "data/raw/sales_train_evaluation.csv",
        "validation": root / "data/raw/sales_train_validation.csv",
        "calendar": root / "data/raw/calendar.csv",
        "prices": root / "data/raw/sell_prices.csv",
        "sample_submission": root / "data/raw/sample_submission.csv",
    }


def select_sales_file(
    paths: dict[str, Path],
    preferred: str,
    fallback: str,
) -> Path:
    """Select the preferred sales file, otherwise the fallback."""
    name_to_key = {
        "sales_train_evaluation.csv": "evaluation",
        "sales_train_validation.csv": "validation",
    }
    preferred_path = paths[name_to_key.get(preferred, "evaluation")]
    fallback_path = paths[name_to_key.get(fallback, "validation")]

    if preferred_path.exists():
        return preferred_path
    if fallback_path.exists():
        return fallback_path

    raise FileNotFoundError(
        "Missing required sales file. Tried:\n"
        f"  {preferred_path}\n"
        f"  {fallback_path}"
    )


def load_calendar(path: Path) -> pd.DataFrame:
    """Load the calendar table with compact dtypes."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    return df


def load_prices(path: Path) -> pd.DataFrame:
    """Load sell prices using compact numeric dtypes."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    df = pd.read_csv(path)
    df["sell_price"] = pd.to_numeric(
        df["sell_price"], errors="coerce"
    ).astype("float32")
    df["wm_yr_wk"] = pd.to_numeric(
        df["wm_yr_wk"], errors="coerce"
    ).astype("int32")
    return df


def _read_sales_header(sales_path: Path) -> tuple[list[str], list[str]]:
    """Return daily demand columns and all columns without loading data rows."""
    header = pd.read_csv(sales_path, nrows=0)
    validate_sales_columns(header.columns)
    day_cols = [c for c in header.columns if c.startswith("d_")]
    if not day_cols:
        raise ValueError(
            f"No daily demand columns beginning with 'd_' found in {sales_path}."
        )
    return list(header.columns), day_cols




def _score_rows(
    frame: pd.DataFrame,
    columns: list[str],
) -> pd.Series:
    """Calculate row-level demand scores with supported pandas APIs."""
    return (
        frame[columns]
        .sum(axis=1, numeric_only=True)
        .astype("float32")
    )

def choose_top_series(
    sales_path: Path,
    max_items_per_store: int,
    max_total_series: int,
    selection_days: int,
    chunk_rows: int,
) -> list[str]:
    """Select high-demand series without fragmenting large DataFrames.

    Ranking is deterministic: highest recent demand first, then ``id`` as a
    tie-breaker. Demand scores are computed in temporary chunk-local objects;
    no new column is inserted into the wide sales frame.
    """
    if not sales_path.exists():
        raise FileNotFoundError(f"Missing required sales file: {sales_path}")
    if max_items_per_store < 1:
        raise ValueError("max_items_per_store must be at least 1")
    if max_total_series < 1:
        raise ValueError("max_total_series must be at least 1")
    if chunk_rows < 1:
        raise ValueError("chunk_rows must be at least 1")

    _, day_cols = _read_sales_header(sales_path)
    if selection_days <= 0 or selection_days >= len(day_cols):
        tail_cols = day_cols
    else:
        tail_cols = day_cols[-selection_days:]

    usecols = ["id", "store_id", "item_id", *tail_cols]
    score_frames: list[pd.DataFrame] = []

    for chunk in pd.read_csv(
        sales_path,
        usecols=usecols,
        chunksize=chunk_rows,
        low_memory=False,
    ):
        # Sum first, then construct a new compact score frame.  This avoids
        # DataFrame.insert-style fragmentation on the wide chunk.
        demand_matrix = chunk[tail_cols].apply(
            pd.to_numeric,
            errors="coerce",
        ).fillna(0).astype("float32")
        selection_demand = demand_matrix.sum(
            axis=1,
            numeric_only=True,
        ).astype("float32")

        score_frames.append(
            pd.DataFrame(
                {
                    "id": chunk["id"].astype("string").to_numpy(),
                    "store_id": chunk["store_id"].astype("string").to_numpy(),
                    "item_id": chunk["item_id"].astype("string").to_numpy(),
                    "selection_demand": selection_demand.to_numpy(),
                }
            )
        )

    if not score_frames:
        raise ValueError("No sales rows were read from the sales file.")

    scores = pd.concat(
        score_frames,
        ignore_index=True,
        copy=False,
    )

    # One global ranking after all chunk scores are collected guarantees that
    # chunk boundaries do not change the selected portfolio.
    scores = scores.sort_values(
        ["store_id", "selection_demand", "id"],
        ascending=[True, False, True],
        kind="mergesort",
    )

    selected = scores.groupby(
        "store_id",
        sort=True,
        observed=True,
    ).head(max_items_per_store)

    selected = selected.sort_values(
        ["selection_demand", "id"],
        ascending=[False, True],
        kind="mergesort",
    ).head(max_total_series)

    return selected["id"].astype(str).tolist()


def load_selected_sales_long(
    sales_path: Path,
    selected_ids: set[str],
    chunk_rows: int,
) -> pd.DataFrame:
    """Load only selected M5 series and convert them to long form.

    The full 30,490-series matrix is never melted. Only selected rows are
    melted inside each chunk, keeping memory use manageable on a 15 GB RAM
    machine.
    """
    if not selected_ids:
        raise ValueError("selected_ids cannot be empty")
    if not sales_path.exists():
        raise FileNotFoundError(f"Missing required sales file: {sales_path}")

    _, day_cols = _read_sales_header(sales_path)
    usecols = [*REQUIRED_META_COLUMNS, *day_cols]
    frames: list[pd.DataFrame] = []

    for chunk in pd.read_csv(
        sales_path,
        usecols=usecols,
        chunksize=chunk_rows,
        low_memory=False,
    ):
        selected = chunk.loc[
            chunk["id"].isin(selected_ids)
        ].copy()
        if selected.empty:
            continue

        long_df = selected.melt(
            id_vars=REQUIRED_META_COLUMNS,
            value_vars=day_cols,
            var_name="d",
            value_name="demand",
        )
        long_df["demand"] = (
            pd.to_numeric(
                long_df["demand"],
                errors="coerce",
            )
            .fillna(0)
            .astype("int16")
        )
        frames.append(long_df)

    if not frames:
        raise ValueError(
            "No selected series were found in the sales file."
        )

    return pd.concat(
        frames,
        ignore_index=True,
        copy=False,
    )
