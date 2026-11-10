# Advanced Statistical Methodology

## New evaluation utilities

- `scripts/run_rolling_backtest.py`: chronological multi-origin forecast evaluation.
- `scripts/run_advanced_evaluation.py`: Croston SBA comparison and empirical interval coverage/width diagnostics.
- `scripts/run_forecast_driven_inventory.py`: separates validation residual calibration from policy selection, freezes the selected policy, and evaluates it on held-out test demand.
- `src/uncertainty/conformal.py`: finite-sample split-conformal residual quantiles and contiguous block-error calibration.
- `src/inventory/forecast_policy.py`: computes periodic-review targets from forecast demand over lead time plus review period and empirical block-residual quantiles.

## Intermittent demand

Croston's method and the Syntetos-Boylan Approximation (SBA) are additional baselines. Compare them by item-store demand segment; neither is assumed to outperform the global model.

## Conformal uncertainty

Absolute out-of-sample residuals are calibrated using a finite-sample order statistic. For inventory, contiguous residuals are aggregated over the protection period before computing an empirical quantile. This is more decision-relevant than applying a single daily residual standard deviation to every horizon.

Classical split-conformal coverage assumes exchangeability. Retail time series exhibit dependence and drift, so empirical coverage and interval width must be measured on later chronological data and rolling origins. The calibration report is diagnostic, not proof of a universal coverage guarantee.

## Forecast-driven inventory

The forecast-driven comparison splits the 28-day validation window chronologically:
1. The first half calibrates residual uncertainty.
2. The second half selects service level and review period using simulated cost.
3. The selected policy is frozen before the held-out test period.
4. Test demand is used only by the simulator to score the frozen policy.

Forecast rows are one-step-ahead predictions with lag features available at each date. This represents rolling replenishment decisions where yesterday's demand is observed before today's review. It is not a fixed-origin multi-week forecast. Review periods are limited to those whose protection period fits in the policy-selection window.

## Rolling-origin backtesting

Run `python -m scripts.run_rolling_backtest` to create `reports/tables/rolling_origin_backtest.csv`. The current implementation evaluates successive chronological windows using the trained validation model. It does not refit the model at every origin; treat it as a fixed-model temporal robustness check rather than full retraining backtesting.

## Interpretation

All cost results remain simulated under documented assumptions. Report forecast metrics, interval coverage, interval width, fill rate, and inventory costs together. Do not describe simulated savings as realized retailer savings.
