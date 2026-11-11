import pandas as pd

from scripts.run_rolling_backtest import paired_cluster_bootstrap


def test_paired_cluster_bootstrap_detects_lower_candidate_error():
    rows = []
    for series_id in range(12):
        actual = [10.0, 12.0, 8.0]
        for date, value in zip(pd.date_range("2024-01-01", periods=3), actual):
            rows.append({
                "id": f"series-{series_id}",
                "date": date,
                "demand": value,
                "xgboost": value + 1.0,
                "seasonal_naive": value + 3.0,
            })
    result = paired_cluster_bootstrap(
        pd.DataFrame(rows), "xgboost", "seasonal_naive",
        n_bootstrap=500, seed=7,
    )
    assert result["series_count"] == 12
    assert result["mean_wape_delta_pp"] < 0
    assert result["ci_95_high_pp"] < 0
    assert result["bootstrap_p_two_sided"] < 0.05


def test_paired_cluster_bootstrap_returns_nan_for_single_series():
    frame = pd.DataFrame({
        "id": ["only", "only"],
        "demand": [10.0, 12.0],
        "model_a": [9.0, 11.0],
        "model_b": [8.0, 10.0],
    })
    result = paired_cluster_bootstrap(frame, "model_a", "model_b", n_bootstrap=100)
    assert result["series_count"] == 1
    assert pd.isna(result["mean_wape_delta_pp"])
