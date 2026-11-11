"""Rolling-origin evaluation on chronological 28-day windows."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from src.features.feature_pipeline import MODEL_FEATURES
from src.forecasting.evaluate import evaluate
from src.forecasting.intermittent import croston_forecast
from src.utils.config import ROOT, load_yaml


def main():
    cfg = load_yaml("model_config.yaml")
    path = ROOT / "data/processed/forecast_features.parquet"
    model_path = ROOT / "models/forecasting/validation_model.joblib"
    if not path.exists() or not model_path.exists():
        raise FileNotFoundError("Run build_features and train_models first.")
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["id", "date"])
    bundle = joblib.load(model_path)
    unique_dates = pd.DatetimeIndex(sorted(pd.to_datetime(df.date).unique()))
    horizon = int(cfg["test_days"])
    initial = max(365, len(unique_dates) - 4 * horizon)
    rows = []
    origin = initial
    fold = 1
    while origin + horizon <= len(unique_dates):
        start, end = unique_dates[origin], unique_dates[origin + horizon - 1]
        window = df[(df.date >= start) & (df.date <= end)].copy()
        window["prediction"] = np.maximum(0, bundle["model"].predict(window[MODEL_FEATURES]))
        metrics = evaluate(window.demand, window.prediction)
        rows.append({"fold": fold, "train_end": str(unique_dates[origin - 1].date()),
                     "test_start": str(start.date()), "test_end": str(end.date()),
                     "model": bundle["model_name"], **metrics})
        fold += 1
        origin += horizon
    if not rows:
        raise RuntimeError("Not enough dates for rolling-origin evaluation.")
    out = ROOT / "reports/tables"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "rolling_origin_backtest.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
