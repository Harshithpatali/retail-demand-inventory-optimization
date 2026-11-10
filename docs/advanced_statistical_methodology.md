# Advanced Statistical Methodology

## New evaluation utilities

- `scripts/run_rolling_backtest.py`: chronological 28-day rolling-origin evaluation.
- `scripts/run_advanced_evaluation.py`: adds Croston SBA comparisons and empirical interval coverage/width diagnostics.
- `scripts/run_forecast_driven_inventory.py`: selects inventory policies on validation forecasts and residuals, then evaluates on the held-out test period.
- `src/uncertainty/conformal.py`: finite-sample split-conformal residual quantiles and contiguous block-error calibration.
- `src/inventory/forecast_policy.py`: computes the periodic-review target from forecast demand over lead time + review period plus an empirical block-residual quantile.

## Intermittent demand

Croston's method and the Syntetos-Boylan Approximation (SBA) are added as baselines. They should be compared by item-store demand segment; no assumption is made that they outperform the global model.

## Conformal uncertainty

Absolute out-of-sample residuals are calibrated using a finite-sample order statistic. For inventory, contiguous residuals are aggregated over the protection period before computing an empirical quantile. This is more decision-relevant than applying a single daily residual standard deviation to every forecast horizon.

The classical split-conformal coverage guarantee assumes exchangeability. Retail time series exhibit dependence and drift, so empirical coverage and interval width must be measured on later chronological data and rolling origins. The reported calibration is diagnostic, not proof of a universal coverage guarantee.

## Forecast-driven inventory

The new comparison evaluates:
1. A historical-statistics baseline.
2. A forecast-driven policy using validation-only policy selection and residual calibration.
3. A separate held-out test simulation using actual test demand only for scoring.

The forecast rows are one-step-ahead predictions using lag features available at each date. This matches a rolling operational setting in which yesterday's demand is observed before today's replenishment decision. It is not a fixed-origin multi-step forecast.

## Rolling-origin backtesting

Run `python -m scripts.run_rolling_backtest` to create `reports/tables/rolling_origin_backtest.csv`. The current helper uses chronological origins and non-overlapping evaluation windows. For deployment decisions, add more origins and compare seasonal regimes where sufficient history exists.

## Interpretation

All cost results remain simulated under documented assumptions. Report forecast metrics, interval coverage, interval width, fill rate, and inventory costs together. Do not describe simulated savings as realized retailer savings.
