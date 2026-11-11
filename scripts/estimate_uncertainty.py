import joblib
import numpy as np
import pandas as pd

from src.utils.config import ROOT, load_yaml
from src.forecasting.evaluate import evaluate
from src.uncertainty.demand_distribution import residual_statistics


def main():
    model_cfg = load_yaml("model_config.yaml")
    features = ROOT / "data/processed/forecast_features.parquet"
    artifact = ROOT / "models/forecasting/validation_model.joblib"
    if not features.exists() or not artifact.exists():
        raise FileNotFoundError(
            "Missing forecasting artifacts. Run python -m scripts.train_models first."
        )

    df = pd.read_parquet(features)
    max_date = df.date.max()
    test_start = max_date - pd.Timedelta(days=model_cfg["test_days"] - 1)
    val_start = test_start - pd.Timedelta(days=model_cfg["validation_days"])
    validation = df[(df.date >= val_start) & (df.date < test_start)]
    bundle = joblib.load(artifact)
    predictions = bundle["model"].predict(
        validation[bundle["feature_columns"]]
    ).clip(min=0)
    residuals = validation["demand"].to_numpy(dtype=float) - predictions
    stats = residual_statistics(residuals)
    stats.update(evaluate(validation["demand"], predictions))
    stats.update({
        "period_start": str(validation.date.min().date()),
        "period_end": str(validation.date.max().date()),
        "source": "out_of_sample_validation",
        # Keep calibration observations so the live service can form an
        # empirical 90% interval rather than assuming Gaussian residuals.
        "calibration_abs_residuals": np.abs(residuals).astype(float).tolist(),
        "calibration_method": "split_conformal_absolute_residual",
        "nominal_coverage": 0.90,
    })
    output = ROOT / "models/uncertainty/residual_stats.joblib"
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(stats, output)
    print({
        "n": stats["n"],
        "std": stats["std"],
        "mae": stats["mae"],
        "calibration_observations": len(stats["calibration_abs_residuals"]),
        "period_start": stats["period_start"],
        "period_end": stats["period_end"],
        "artifact": str(output),
    })


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
