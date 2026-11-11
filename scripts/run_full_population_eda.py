"""Full-population M5 exploratory analysis without materializing a long panel.

Reads the complete wide sales matrix in row chunks and emits compact CSV
summaries, a Markdown report and publication-ready plots for all item-store
series. It intentionally does not change the 200-series modelling dataset.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.config import ROOT

RAW = ROOT / "data" / "raw"
OUT = ROOT / "reports" / "eda" / "full_data"
FIG = OUT / "figures"
META = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
CHUNK_ROWS = 256


def _sales_file() -> Path:
    for name in ("sales_train_evaluation.csv", "sales_train_validation.csv"):
        path = RAW / name
        if path.exists():
            return path
    raise FileNotFoundError("Full M5 sales matrix not found in data/raw/.")


def _save_plot(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _read_sales_header(path: Path) -> tuple[list[str], list[str]]:
    columns = list(pd.read_csv(path, nrows=0).columns)
    date_cols = [c for c in columns if re.fullmatch(r"d_\d+", c)]
    missing = set(META) - set(columns)
    if missing or not date_cols:
        raise ValueError(f"Unexpected sales schema; missing={sorted(missing)}, date columns={len(date_cols)}")
    return columns, date_cols


def _population_analysis(path: Path, date_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_series: list[pd.DataFrame] = []
    daily_total = np.zeros(len(date_cols), dtype=np.float64)
    daily_nonzero_series = np.zeros(len(date_cols), dtype=np.int64)
    daily_observations = 0

    for chunk in pd.read_csv(path, usecols=META + date_cols, chunksize=CHUNK_ROWS):
        values = chunk[date_cols].to_numpy(dtype=np.float32, copy=False)
        daily_total += values.sum(axis=0, dtype=np.float64)
        daily_nonzero_series += (values > 0).sum(axis=0)
        totals = values.sum(axis=1, dtype=np.float64)
        means = values.mean(axis=1, dtype=np.float64)
        stds = values.std(axis=1, dtype=np.float64)
        nonzero = (values > 0).sum(axis=1)
        zero_fraction = 1.0 - nonzero / values.shape[1]
        adi = np.divide(values.shape[1], nonzero, out=np.full(len(chunk), np.inf), where=nonzero > 0)
        cv2 = np.divide(stds, means, out=np.full(len(chunk), np.nan), where=means > 0) ** 2
        metrics = chunk[META].copy()
        metrics["total_units"] = totals
        metrics["mean_daily_demand"] = means
        metrics["std_daily_demand"] = stds
        metrics["max_daily_demand"] = values.max(axis=1)
        metrics["nonzero_days"] = nonzero
        metrics["zero_day_fraction"] = zero_fraction
        metrics["average_demand_interval"] = adi
        metrics["demand_cv_squared"] = cv2
        metrics["active"] = nonzero > 0
        per_series.append(metrics)
        daily_observations += len(chunk)

    series = pd.concat(per_series, ignore_index=True)
    daily = pd.DataFrame({
        "d": date_cols,
        "total_units": daily_total,
        "active_series": daily_nonzero_series,
        "series_count": daily_observations,
    })
    return series, daily


def _write_group_tables(series: pd.DataFrame) -> dict[str, pd.DataFrame]:
    outputs = {}
    for dimension in ("state_id", "store_id", "cat_id", "dept_id"):
        grouped = series.groupby(dimension, observed=True).agg(
            series_count=("id", "nunique"),
            total_units=("total_units", "sum"),
            mean_series_daily_demand=("mean_daily_demand", "mean"),
            median_series_zero_fraction=("zero_day_fraction", "median"),
            median_series_cv_squared=("demand_cv_squared", "median"),
            active_series=("active", "sum"),
        ).reset_index().sort_values("total_units", ascending=False)
        grouped.to_csv(OUT / f"by_{dimension}.csv", index=False)
        outputs[dimension] = grouped
    return outputs


def _price_analysis() -> pd.DataFrame:
    path = RAW / "sell_prices.csv"
    if not path.exists():
        raise FileNotFoundError("sell_prices.csv is required for full-data price EDA.")
    prices = pd.read_csv(path)
    prices["sell_price"] = pd.to_numeric(prices["sell_price"], errors="coerce")
    prices["price_change"] = prices.groupby(["store_id", "item_id"], observed=True)["sell_price"].pct_change()
    summary = prices.groupby("store_id", observed=True).agg(
        price_records=("sell_price", "size"),
        unique_items=("item_id", "nunique"),
        mean_price=("sell_price", "mean"),
        median_price=("sell_price", "median"),
        price_p90=("sell_price", lambda x: x.quantile(0.90)),
        price_missing=("sell_price", lambda x: x.isna().sum()),
    ).reset_index()
    summary.to_csv(OUT / "price_summary_by_store.csv", index=False)
    prices[["sell_price", "price_change"]].describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).to_csv(OUT / "price_distribution.csv")
    return prices


def _calendar_analysis(daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    calendar = pd.read_csv(RAW / "calendar.csv")
    calendar["date"] = pd.to_datetime(calendar["date"])
    daily["date"] = pd.to_datetime(daily["d"].str.replace("d_", "", regex=False).astype(int), unit="D", origin="2011-01-29")
    merged = daily.merge(calendar, on="date", how="left", validate="one_to_one")
    merged["month_label"] = merged["date"].dt.to_period("M").astype(str)
    merged["weekday_name"] = merged["date"].dt.day_name()
    monthly = merged.groupby("month_label", observed=True).agg(
        total_units=("total_units", "sum"),
        mean_daily_units=("total_units", "mean"),
        mean_active_series=("active_series", "mean"),
    ).reset_index()
    weekday = merged.groupby("weekday_name", observed=True).agg(
        mean_daily_units=("total_units", "mean"),
        median_daily_units=("total_units", "median"),
        mean_active_series=("active_series", "mean"),
    ).reindex(["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]).reset_index()
    merged.to_csv(OUT / "daily_demand_full_population.csv", index=False)
    monthly.to_csv(OUT / "monthly_demand.csv", index=False)
    weekday.to_csv(OUT / "weekday_demand.csv", index=False)
    return monthly, weekday


def _make_plots(series, daily, groups, monthly, weekday, prices) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(daily["date"], daily["total_units"], linewidth=.8)
    ax.set(title="M5 total daily unit sales — full item-store population", xlabel="Date", ylabel="Units")
    _save_plot(fig, "01_daily_total_demand.png")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(monthly["month_label"], monthly["mean_daily_units"], marker="o", markersize=2)
    ax.set(title="Monthly average daily demand", xlabel="Month", ylabel="Average daily units")
    ax.tick_params(axis="x", labelrotation=70)
    _save_plot(fig, "02_monthly_demand.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(weekday["weekday_name"], weekday["mean_daily_units"])
    ax.set(title="Average demand by weekday", ylabel="Average daily units")
    ax.tick_params(axis="x", labelrotation=30)
    _save_plot(fig, "03_weekday_seasonality.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(series["total_units"], bins=70, log=True)
    ax.set(title="Distribution of cumulative demand by item-store series", xlabel="Total units across history", ylabel="Series count (log scale)")
    _save_plot(fig, "04_series_total_distribution.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(series["zero_day_fraction"], bins=50)
    ax.set(title="Intermittency across item-store series", xlabel="Fraction of days with zero sales", ylabel="Series count")
    _save_plot(fig, "05_zero_demand_fraction.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(series["average_demand_interval"].replace(np.inf, np.nan), series["demand_cv_squared"], s=5, alpha=.25)
    ax.set(xscale="log", yscale="log", title="Intermittency diagnostics (ADI vs squared CV)", xlabel="Average demand interval (days)", ylabel="Squared coefficient of variation")
    _save_plot(fig, "06_adi_cv2.png")

    for dimension, title in (("state_id", "State"), ("store_id", "Store"), ("cat_id", "Category"), ("dept_id", "Department")):
        frame = groups[dimension].head(20).sort_values("total_units")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(frame[dimension].astype(str), frame["total_units"])
        ax.set(title=f"Top demand contributors by {title.lower()}", xlabel="Total units")
        _save_plot(fig, f"07_{dimension}_demand.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    clean = prices["sell_price"].dropna()
    ax.hist(clean.clip(upper=clean.quantile(.99)), bins=60)
    ax.set(title="Sell-price distribution (winsorized at 99th percentile for display)", xlabel="Sell price", ylabel="Price records")
    _save_plot(fig, "08_price_distribution.png")


def _report(series, daily, monthly, weekday, prices, sales_path, date_cols) -> None:
    total = float(series["total_units"].sum())
    active = int(series["active"].sum())
    report = {
        "source_sales_file": sales_path.name,
        "series_count": int(series["id"].nunique()),
        "date_count": len(date_cols),
        "first_date": str(daily["date"].min().date()),
        "last_date": str(daily["date"].max().date()),
        "total_units": total,
        "active_series": active,
        "inactive_series": int(len(series) - active),
        "series_zero_fraction_median": float(series["zero_day_fraction"].median()),
        "series_zero_fraction_mean": float(series["zero_day_fraction"].mean()),
        "series_total_demand_median": float(series["total_units"].median()),
        "price_records": int(len(prices)),
        "price_missing_values": int(prices["sell_price"].isna().sum()),
    }
    (OUT / "full_eda_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    text = f"""# Full-population M5 exploratory data analysis

## Scope
- Source: `{sales_path.name}`
- Population: **{report['series_count']:,} item-store series**
- Daily observations per series: **{len(date_cols):,}**
- Date range: **{report['first_date']} to {report['last_date']}**
- Total recorded sales: **{total:,.0f} units**
- Active series: **{active:,}**; no-sales series: **{len(series)-active:,}**

## Demand profile
- Median series zero-day fraction: **{report['series_zero_fraction_median']:.1%}**
- Mean series zero-day fraction: **{report['series_zero_fraction_mean']:.1%}**
- Median cumulative series demand: **{report['series_total_demand_median']:,.1f} units**
- Median daily active series: **{daily['active_series'].median():,.0f}**

## Price data
- Price records: **{len(prices):,}**
- Missing sell prices: **{prices['sell_price'].isna().sum():,}**

## Generated outputs
- `full_eda_summary.json`: headline metrics
- `series_metrics.csv`: all series-level demand and intermittency metrics
- `daily_demand_full_population.csv`: daily aggregate and calendar attributes
- `by_state_id.csv`, `by_store_id.csv`, `by_cat_id.csv`, `by_dept_id.csv`: segment summaries
- `monthly_demand.csv`, `weekday_demand.csv`: temporal summaries
- `price_summary_by_store.csv`, `price_distribution.csv`: price summaries
- `figures/`: full-population plots

## Interpretation and limitations
This EDA uses the full supplied M5 evaluation sales matrix rather than the project's 200-series modelling subset. Sales are observed unit counts; zeros are retained and interpreted as no recorded sales, not necessarily proof of no demand. M5 is a competition dataset with historical prices and calendar/event fields; it does not include verified store coordinates, inventory positions, replenishment lead times, or realized operating costs. Segment aggregates are descriptive and do not establish causal effects.
"""
    (OUT / "FULL_DATA_EDA.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sales_path = _sales_file()
    _, date_cols = _read_sales_header(sales_path)
    print(f"Analysing {sales_path.name}: all series, {len(date_cols)} daily columns.")
    series, daily = _population_analysis(sales_path, date_cols)
    series.to_csv(OUT / "series_metrics.csv", index=False)
    groups = _write_group_tables(series)
    monthly, weekday = _calendar_analysis(daily)
    prices = _price_analysis()
    _make_plots(series, daily.assign(date=pd.to_datetime(daily["d"].str.replace("d_", "", regex=False).astype(int), unit="D", origin="2011-01-29")), groups, monthly, weekday, prices)
    _report(series, pd.read_csv(OUT / "daily_demand_full_population.csv", parse_dates=["date"]), monthly, weekday, prices, sales_path, date_cols)
    print(f"Full EDA complete: {len(series):,} series, {len(date_cols):,} days.")
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
