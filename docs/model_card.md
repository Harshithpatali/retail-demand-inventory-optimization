# Model Card — Retail Demand Forecasting & Inventory Optimization

## Intended use

Historical demand forecasting, forecast uncertainty diagnostics and replenishment-policy comparison for analyst decision support. The model is a research prototype for a controlled shadow evaluation; it is not an autonomous ordering system.

## Data and scope

- Dataset: M5 Forecasting — Accuracy (Walmart item-store daily sales, calendar and selling-price data).
- Full-population descriptive EDA: 30,490 item-store series.
- Forecasting and inventory experiments: deterministic selected panel of 200 item-store series.
- Rolling-origin refit evaluation: four 28-day origins, 22,400 pooled out-of-fold observations.
- Final inventory policy evaluation: 28-day rolling one-step-ahead simulation.

## Methods

- XGBoost and LightGBM global demand regressors.
- Naive, seasonal-naive, 7-day moving-average and Croston SBA reference methods.
- Lagged and rolling features with chronological training.
- Expanding-window rolling-origin refit and paired item-store cluster bootstrap.
- Residual-based conformal interval diagnostics using prior chronological validation residuals.
- Periodic-review inventory simulation with explicit holding, ordering and stockout cost assumptions.

## Reported empirical results

### Forecasting

| Method | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| XGBoost, refit per origin | 7.074 | 10.960 | 29.11% |
| LightGBM, refit per origin | 7.132 | 11.007 | 29.35% |
| 7-day moving average | 8.383 | 13.030 | 34.49% |
| Naive | 9.386 | 14.845 | 38.62% |
| 7-day seasonal naive | 9.793 | 15.646 | 40.29% |

The paired series-cluster bootstrap reports an XGBoost minus moving-average mean per-series WAPE difference of -4.875 percentage points (95% percentile interval -5.343 to -4.412) across the selected panel.

### Inventory simulation

On the final 28-day test simulation, the forecast-driven policy versus historical-demand baseline reported mean per-series cost 246.95 versus 299.76 (-17.62%), stockout units 43.10 versus 53.92 (-20.05%), average ending inventory 90.12 versus 122.95 (-26.70%), and fill rate 94.21% versus 93.88% (+0.32 percentage points).

These are simulated outcomes under repository-defined cost assumptions, not realized savings.

### Interval diagnostics

Empirical held-out coverage was 82.43%, 92.59% and 95.91% for nominal 80%, 90% and 95% intervals respectively. Time-series dependence and non-stationarity mean these are diagnostics, not guaranteed future coverage.

## Known limitations

- Only 200 of 30,490 item-store series are used for model evaluation.
- Results depend on a specific historical M5 period and may not generalize under distribution shift.
- Inventory evaluation is a short rolling one-step simulation; it is not a full operational replenishment trial.
- Supplier lead-time uncertainty, minimum order quantities, capacity constraints and real store/warehouse assignments are not fully observed.
- Holding, ordering and stockout costs are assumed inputs.
- The full-population EDA is descriptive and must not be presented as full-population model validation.

## Business interpretation

The project tests whether better demand ranking and uncertainty estimates can reduce the trade-off between inventory availability and working capital. In the evaluated panel, the forecast-driven policy improved simulated cost, stockouts and inventory while slightly increasing fill rate. A real pilot requires retailer SKU-store data, measured lead-time distributions, finance-approved cost inputs and comparison with current planner decisions.

## Reproducibility

```bash
pip install -r requirements.txt
pytest -q
python -m scripts.train_models
python -m scripts.estimate_uncertainty
python -m scripts.run_forecast_driven_inventory
```

The source M5 archive is retrieved through the documented private Supabase Storage workflow. Keep its credentials in GitHub Actions secrets, not in the repository.