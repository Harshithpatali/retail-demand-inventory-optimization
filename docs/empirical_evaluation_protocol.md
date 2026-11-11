# Empirical evaluation protocol and interpretation

## Verified application state
The live Streamlit UI, map and inventory gauge have been visually checked by the project owner. This is a UI verification, separate from model evaluation.

## Reproducible experiments
The `empirical-evaluation` GitHub Actions workflow runs against the committed processed M5 feature panel and validation model. It creates:

- `rolling_origin_backtest.csv`: four successive chronological windows using the saved validation model. The model is held fixed; it is a temporal robustness check, not refitting at every origin.
- `advanced_forecast_metrics.csv`: held-out one-step-ahead model metrics compared with rolling one-step Croston SBA.
- `conformal_interval_diagnostics.csv`: empirical coverage and mean width at 80%, 90% and 95% nominal levels, calibrated on the prior validation window.
- `forecast_metrics_by_demand_segment.csv`: error metrics across low-, medium- and high-volume series.
- `forecast_driven_inventory_comparison.csv`: historical baseline versus forecast-informed periodic-review policy on the held-out test window. Calibration and policy selection are separated within validation.
- `inventory_sensitivity_summary.csv`: test-period inventory outcomes across lead times, target service levels and cost scenarios.

## Inventory sensitivity design
The sensitivity experiment uses a deterministic sample of up to 30 item-store series spanning the training-volume distribution. It varies lead time (1, 3, 5, 7, 10, 14, 21 and 30 days), target service level (80%, 85%, 90%, 95% and 97%), and five transparent cost scenarios. For each lead time and cost scenario, candidate service levels are compared with an 80% target policy using the same test demand. This isolates service-level policy sensitivity; it does not claim that the target fill rate is achieved.

## Statistical cautions
- The rolling-origin script uses a fixed saved model; model retraining at each origin is not performed.
- The model and Croston SBA are compared as rolling one-step-ahead predictions. This is not a fixed-origin multi-week forecast competition.
- Conformal intervals use chronological validation residuals. Time-series dependence and distribution drift invalidate a blanket exchangeability guarantee; empirical coverage is reported as a diagnostic.
- Inventory results are simulations, not realized retailer savings. Holding, ordering and stockout costs are assumptions.
- The sensitivity sample is capped at 30 series for bounded runtime. Results should be described as a sample-level robustness analysis, not a full-panel estimate.

## Run locally
```bash
python -m scripts.run_rolling_backtest
python -m scripts.run_advanced_evaluation
python -m scripts.run_forecast_driven_inventory
python -m scripts.run_inventory_sensitivity
```

The GitHub Actions workflow uploads the generated CSV tables as a downloadable artifact.
