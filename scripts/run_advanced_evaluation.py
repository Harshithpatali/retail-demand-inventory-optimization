"""Chronological holdout diagnostics: model vs Croston SBA and conformal intervals."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from src.features.feature_pipeline import MODEL_FEATURES
from src.forecasting.evaluate import evaluate
from src.forecasting.intermittent import croston_forecast
from src.uncertainty.conformal import interval_bounds
from src.utils.config import ROOT, load_yaml


def main() -> None:
    cfg = load_yaml("model_config.yaml")
    data_path = ROOT / "data/processed/forecast_features.parquet"
    model_path = ROOT / "models/forecasting/validation_model.joblib"
    if not data_path.exists() or not model_path.exists():
        raise FileNotFoundError("Run build_features and train_models first.")

    df = pd.read_parquet(data_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["id", "date"])
    dates = pd.DatetimeIndex(sorted(df["date"].unique()))
    test_days = int(cfg["test_days"])
    validation_days = int(cfg["validation_days"])
    test_start = dates[-test_days]
    validation_start = dates[-(test_days + validation_days)]
    validation = df[(df.date >= validation_start) & (df.date < test_start)].copy()
    test = df[df.date >= test_start].copy()
    if validation.empty or test.empty:
        raise RuntimeError("Chronological validation/test windows are empty.")

    bundle = joblib.load(model_path)
    model_name = str(bundle.get("model_name", "trained_model"))
    validation["prediction"] = np.maximum(
        0.0, bundle["model"].predict(validation[MODEL_FEATURES])
    )
    test["prediction"] = np.maximum(0.0, bundle["model"].predict(test[MODEL_FEATURES]))
    validation["residual"] = validation["demand"].to_numpy() - validation["prediction"].to_numpy()

    # Rolling one-step Croston SBA: only observations strictly before each test date.
    sba_predictions = []
    for sid, group in test.groupby("id", observed=True):
        full_series = df[df.id == sid].sort_values("date")
        history = full_series.set_index("date")["demand"]
        for row in group.sort_values("date").itertuples():
            past = history.loc[history.index < row.date].to_numpy(dtype=float)
            sba_predictions.append((sid, row.date, float(croston_forecast(past, 1, sba=True)[0])))
    sba = pd.DataFrame(sba_predictions, columns=["id", "date", "croston_sba_prediction"])
    test = test.merge(sba, on=["id", "date"], how="left", validate="one_to_one")

    metrics = []
    for name, prediction in [
        (model_name, test["prediction"]),
        ("croston_sba_rolling_one_step", test["croston_sba_prediction"]),
    ]:
        metrics.append({"model": name, **evaluate(test["demand"], prediction)})

    # Per-series calibration where available; otherwise use pooled calibration residuals.
    pooled = validation["residual"].to_numpy(dtype=float)
    interval_rows = []
    for coverage in (0.80, 0.90, 0.95):
        lows, highs, actuals = [], [], []
        for sid, group in test.groupby("id", observed=True):
            calibration = validation.loc[validation.id == sid, "residual"].to_numpy(dtype=float)
            if len(calibration) < 8:
                calibration = pooled
            lo, hi = interval_bounds(group["prediction"].to_numpy(), calibration, coverage)
            lows.extend(lo.tolist())
            highs.extend(hi.tolist())
            actuals.extend(group["demand"].to_numpy(dtype=float).tolist())
        low = np.asarray(lows)
        high = np.asarray(highs)
        actual = np.asarray(actuals)
        interval_rows.append({
            "nominal_coverage": coverage,
            "empirical_coverage": float(np.mean((actual >= low) & (actual <= high))),
            "mean_interval_width": float(np.mean(high - low)),
            "observations": int(len(actual)),
            "calibration": "per-series validation residuals; pooled fallback below 8 scores",
        })

    out = ROOT / "reports/tables"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(metrics).to_csv(out / "advanced_forecast_metrics.csv", index=False)
    pd.DataFrame(interval_rows).to_csv(out / "conformal_interval_diagnostics.csv", index=False)

    segment = test[["id", "demand", "prediction"]].copy()
    segment["absolute_error"] = np.abs(segment["demand"] - segment["prediction"])
    volume = segment.groupby("id", observed=True)["demand"].sum().rename("series_volume")
    segment = segment.join(volume, on="id")
    segment["demand_segment"] = pd.qcut(
        segment["series_volume"], q=[0, 0.5, 0.8, 1.0],
        labels=["low", "medium", "high"], duplicates="drop",
    )
    segment_rows = []
    for label, group in segment.groupby("demand_segment", observed=True):
        segment_rows.append({"demand_segment": str(label), **evaluate(group.demand, group.prediction)})
    pd.DataFrame(segment_rows).to_csv(out / "forecast_metrics_by_demand_segment.csv", index=False)

    print("Forecast metrics (held-out chronological window)")
    print(pd.DataFrame(metrics).to_string(index=False))
    print("\nConformal interval diagnostics")
    print(pd.DataFrame(interval_rows).to_string(index=False))
    print("\nMetrics by demand segment")
    print(pd.DataFrame(segment_rows).to_string(index=False))


if __name__ == "__main__":
    main()
