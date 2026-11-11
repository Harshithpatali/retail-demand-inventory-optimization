"""Expanding-window rolling-origin backtest with model refitting at every origin.

Each fold trains XGBoost and LightGBM using only observations dated before
the origin, then scores the next fixed horizon. Seasonal-naive and simple
baselines use only each series' history available at that origin.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from src.features.feature_pipeline import MODEL_FEATURES
from src.forecasting.baselines import (
    moving_average_forecast,
    naive_forecast,
    seasonal_naive_forecast,
)
from src.forecasting.evaluate import evaluate
from src.forecasting.lightgbm_model import build_lightgbm
from src.forecasting.xgboost_model import build_xgboost
from src.utils.config import ROOT, load_yaml


BASELINES = ("naive", "seasonal_naive", "moving_average")
MODELS = ("xgboost", "lightgbm")


def _predict_baselines(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, np.ndarray]:
    """Create strictly historical per-series baseline forecasts in test row order."""
    predictions = {name: np.zeros(len(test), dtype=float) for name in BASELINES}
    test_positions = pd.Series(np.arange(len(test)), index=test.index)
    history = {
        str(series_id): group.sort_values("date")["demand"].astype(float)
        for series_id, group in train.groupby("id", observed=True, sort=False)
    }
    for series_id, rows in test.groupby("id", observed=True, sort=False):
        key = str(series_id)
        hist = history.get(key, pd.Series(dtype=float))
        ordered = rows.sort_values("date")
        positions = test_positions.loc[ordered.index].to_numpy(dtype=int)
        horizon = len(ordered)
        predictions["naive"][positions] = naive_forecast(hist, horizon)
        predictions["seasonal_naive"][positions] = seasonal_naive_forecast(hist, horizon)
        predictions["moving_average"][positions] = moving_average_forecast(hist, horizon)
    return predictions


def _series_wape(frame: pd.DataFrame, prediction_col: str) -> pd.Series:
    grouped = frame.assign(
        abs_error=(frame["demand"] - frame[prediction_col]).abs()
    ).groupby("id", observed=True)
    numerator = grouped["abs_error"].sum()
    denominator = grouped["demand"].apply(lambda values: values.abs().sum())
    return (numerator / denominator.replace(0, np.nan)).dropna()


def paired_cluster_bootstrap(
    frame: pd.DataFrame,
    candidate: str,
    reference: str,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict[str, float]:
    """Paired bootstrap over series; preserves within-series dependence."""
    left = _series_wape(frame, candidate)
    right = _series_wape(frame, reference)
    paired = pd.concat([left.rename("candidate"), right.rename("reference")], axis=1).dropna()
    if len(paired) < 2:
        return {"series_count": int(len(paired)), "mean_wape_delta_pp": float("nan"),
                "ci_95_low_pp": float("nan"), "ci_95_high_pp": float("nan"),
                "bootstrap_p_two_sided": float("nan")}
    delta = (paired["candidate"] - paired["reference"]).to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(delta), size=(n_bootstrap, len(delta)))
    boot = delta[draws].mean(axis=1) * 100
    observed = float(delta.mean() * 100)
    # Add-one correction avoids a zero Monte Carlo p-value.
    p_value = (1 + np.count_nonzero(np.abs(boot) >= abs(observed))) / (n_bootstrap + 1)
    low, high = np.quantile(boot, [0.025, 0.975])
    return {
        "series_count": int(len(delta)),
        "mean_wape_delta_pp": observed,
        "ci_95_low_pp": float(low),
        "ci_95_high_pp": float(high),
        "bootstrap_p_two_sided": float(p_value),
    }


def main() -> None:
    cfg = load_yaml("model_config.yaml")
    data_path = ROOT / "data/processed/forecast_features.parquet"
    if not data_path.is_file():
        raise FileNotFoundError("Run python -m scripts.build_features first.")

    df = pd.read_parquet(data_path)
    required = {"id", "date", "demand", *MODEL_FEATURES}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Forecast feature panel is missing columns: {missing}")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "id"]).reset_index(drop=True)
    dates = pd.DatetimeIndex(sorted(df["date"].unique()))

    horizon = int(cfg["test_days"])
    n_origins = int(cfg.get("rolling_origins", 4))
    first_origin = len(dates) - n_origins * horizon
    if first_origin <= 0:
        raise ValueError("Not enough dates for the configured origins and horizon.")

    fold_rows: list[dict] = []
    prediction_frames: list[pd.DataFrame] = []
    for fold in range(n_origins):
        origin_idx = first_origin + fold * horizon
        origin_date = dates[origin_idx]
        test_end_idx = origin_idx + horizon
        test_dates = dates[origin_idx:test_end_idx]
        if len(test_dates) != horizon:
            raise ValueError(f"Fold {fold + 1} does not contain a complete horizon.")

        train = df.loc[df["date"] < origin_date].copy()
        test = df.loc[df["date"].isin(test_dates)].copy()
        if train.empty or test.empty:
            raise ValueError(f"Fold {fold + 1} has an empty train or test partition.")

        y_train = train["demand"].astype(float)
        fold_predictions = _predict_baselines(train, test)
        for name in MODELS:
            if name == "xgboost":
                model = build_xgboost(cfg["xgboost"], cfg["random_seed"], cfg["n_jobs"])
            else:
                model = build_lightgbm(cfg["lightgbm"], cfg["random_seed"], cfg["n_jobs"])
            model.fit(train[MODEL_FEATURES], y_train)
            fold_predictions[name] = np.maximum(
                0.0, model.predict(test[MODEL_FEATURES]).astype(float)
            )

        scored = test[["id", "date", "demand"]].copy().reset_index(drop=True)
        for name, values in fold_predictions.items():
            scored[name] = np.asarray(values, dtype=float)
            metrics = evaluate(scored["demand"], scored[name])
            fold_rows.append({
                "fold": fold + 1,
                "train_end": str((origin_date - pd.Timedelta(days=1)).date()),
                "test_start": str(test_dates[0].date()),
                "test_end": str(test_dates[-1].date()),
                "training_rows": int(len(train)),
                "test_rows": int(len(test)),
                "series_count": int(test["id"].nunique()),
                "model": name,
                **metrics,
            })
        prediction_frames.append(scored)
        print(
            f"Fold {fold + 1}/{n_origins}: train < {origin_date.date()}, "
            f"test {test_dates[0].date()} to {test_dates[-1].date()}, "
            f"rows {len(train):,}/{len(test):,}"
        )

    output_dir = ROOT / "reports/tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    fold_table = pd.DataFrame(fold_rows)
    fold_table.to_csv(output_dir / "rolling_origin_refit_by_fold.csv", index=False)

    all_predictions = pd.concat(prediction_frames, ignore_index=True)
    overall_rows = []
    for name in (*MODELS, *BASELINES):
        overall_rows.append({
            "model": name,
            **evaluate(all_predictions["demand"], all_predictions[name]),
            "series_count": int(all_predictions["id"].nunique()),
            "observation_count": int(len(all_predictions)),
            "fold_count": int(n_origins),
        })
    overall = pd.DataFrame(overall_rows).sort_values("WAPE")
    overall.to_csv(output_dir / "rolling_origin_refit_summary.csv", index=False)

    comparisons = []
    for reference in ("lightgbm", "seasonal_naive", "moving_average", "naive"):
        result = paired_cluster_bootstrap(
            all_predictions, "xgboost", reference,
            seed=int(cfg["random_seed"]),
        )
        comparisons.append({
            "candidate": "xgboost",
            "reference": reference,
            "interpretation": "negative_delta_favors_xgboost",
            **result,
        })
    pd.DataFrame(comparisons).to_csv(
        output_dir / "rolling_origin_paired_comparisons.csv", index=False
    )

    print("\nPooled rolling-origin results:")
    print(overall.to_string(index=False))
    print("\nPaired series-cluster bootstrap (XGBoost minus reference WAPE, pp):")
    print(pd.DataFrame(comparisons).to_string(index=False))
    print("\nSaved rolling_origin_refit_{by_fold,summary,paired_comparisons}.csv")


if __name__ == "__main__":
    main()
