from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from api.services.artifacts import ArtifactStore

router = APIRouter()
_store = ArtifactStore()


@lru_cache(maxsize=128)
def _eda_payload(store_id: str, item_id: str):
    frame = _store.load_full_series(store_id, item_id)
    if frame.empty:
        return None

    frame = frame.sort_values("date").copy()
    demand = pd.to_numeric(frame["demand"], errors="coerce").fillna(0.0)
    dates = pd.to_datetime(frame["date"])
    frame["demand"] = demand
    frame["date"] = dates

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = (
        frame.assign(weekday=dates.dt.day_name())
        .groupby("weekday")["demand"].agg(["mean", "median", "std", "sum", "count"])
        .reindex(weekday_order).fillna(0).reset_index()
    )
    monthly = (
        frame.assign(month=dates.dt.to_period("M").astype(str))
        .groupby("month")["demand"].agg(["mean", "sum", "std", "count"])
        .reset_index()
    )
    yearly = (
        frame.assign(year=dates.dt.year)
        .groupby("year")["demand"].agg(["mean", "sum", "std", "count"])
        .reset_index()
    )
    month_of_year = (
        frame.assign(month_num=dates.dt.month, month_name=dates.dt.month_name())
        .groupby(["month_num", "month_name"])["demand"].mean()
        .reset_index().sort_values("month_num")
    )

    values = demand.to_numpy(dtype=float)
    hist_counts, hist_edges = np.histogram(values, bins=min(30, max(8, int(np.sqrt(len(values))))))
    prices = pd.to_numeric(frame.get("sell_price"), errors="coerce") if "sell_price" in frame else pd.Series(dtype=float)
    price_corr = None
    if len(prices) == len(demand) and prices.notna().sum() > 2 and prices.nunique(dropna=True) > 1:
        correlation = pd.concat([demand, prices], axis=1).corr().iloc[0, 1]
        price_corr = None if pd.isna(correlation) or not np.isfinite(correlation) else float(correlation)

    def safe_number(value):
        return None if pd.isna(value) or not np.isfinite(value) else float(value)

    def safe_corr(lag: int):
        value = demand.autocorr(lag=lag) if len(demand) > lag + 2 else np.nan
        return safe_number(value)

    def records_without_nan(dataframe: pd.DataFrame):
        clean = dataframe.astype(object).where(pd.notna(dataframe), None)
        return clean.to_dict(orient="records")

    nonzero = demand[demand > 0]
    stats = {
        "observations": int(len(frame)),
        "start_date": dates.min().date().isoformat(),
        "end_date": dates.max().date().isoformat(),
        "total_demand": float(demand.sum()),
        "mean": float(demand.mean()),
        "median": float(demand.median()),
        "std": float(demand.std(ddof=1)) if len(demand) > 1 else 0.0,
        "variance": float(demand.var(ddof=1)) if len(demand) > 1 else 0.0,
        "minimum": float(demand.min()),
        "maximum": float(demand.max()),
        "zero_demand_rate": float((demand == 0).mean()),
        "nonzero_mean": float(nonzero.mean()) if len(nonzero) else 0.0,
        "coefficient_of_variation": float(demand.std(ddof=1) / demand.mean()) if len(demand) > 1 and demand.mean() else 0.0,
        "q25": float(demand.quantile(.25)),
        "q50": float(demand.quantile(.50)),
        "q75": float(demand.quantile(.75)),
        "q90": float(demand.quantile(.90)),
        "q95": float(demand.quantile(.95)),
        "q99": float(demand.quantile(.99)),
        "skewness": safe_number(demand.skew()) if len(demand) > 2 else 0.0,
        "kurtosis": safe_number(demand.kurtosis()) if len(demand) > 3 else 0.0,
        "lag1_autocorrelation": safe_corr(1),
        "lag7_autocorrelation": safe_corr(7),
        "lag28_autocorrelation": safe_corr(28),
        "price_demand_correlation": price_corr,
    }

    daily = [
        {"date": row.date.date().isoformat(), "demand": float(row.demand)}
        for row in frame[["date", "demand"]].itertuples(index=False)
    ]
    return {
        "stats": stats,
        "daily": daily,
        "weekday": records_without_nan(weekday),
        "monthly": records_without_nan(monthly),
        "yearly": records_without_nan(yearly),
        "month_of_year": records_without_nan(month_of_year),
        "histogram": {
            "counts": hist_counts.astype(int).tolist(),
            "edges": hist_edges.astype(float).tolist(),
        },
    }


@router.get("/eda")
def eda(store_id: str, item_id: str):
    """Cached descriptive and temporal EDA for the complete selected series."""
    try:
        payload = _eda_payload(str(store_id), str(item_id))
        if payload is None:
            raise HTTPException(status_code=404, detail="Unknown store_id/item_id combination.")
        return payload
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
