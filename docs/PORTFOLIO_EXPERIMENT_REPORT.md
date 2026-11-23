# Retail forecasting and inventory experiment report

**Dataset:** M5; 30,490 item-store series in full-population EDA.  
**Model experiment scope:** deterministic selected panel of 200 item-store series.  
**Forecast test scope:** four rolling 28-day origins; 22,400 pooled observations.  
**Inventory simulation:** final 28-day holdout, rolling one-step decisions.  
**Status:** historical experiment report; not a claim of realized retailer savings.

## Forecast comparison

| Method | Pooled WAPE |
|---|---:|
| XGBoost, refit at each origin | **29.11%** |
| LightGBM, refit at each origin | 29.35% |
| 7-day moving average | 34.49% |
| Naive | 38.62% |
| 7-day seasonal naive | 40.29% |

The paired item-store cluster bootstrap reports XGBoost minus comparator mean per-series WAPE differences of -0.347 pp versus LightGBM (95% interval [-0.479, -0.200]), -4.875 pp versus moving average ([-5.343, -4.412]), -9.851 pp versus naive ([-10.503, -9.174]), and -12.453 pp versus seasonal naive ([-13.487, -11.528]). The 200 series are the resampling clusters; this does not establish performance on all 30,490 series.

## Inventory policy comparison

On the final 28-day test period, mean per-series simulation results were:

| Metric | Historical-demand baseline | Forecast-driven policy | Relative change |
|---|---:|---:|---:|
| Simulated total cost | 299.76 | 246.95 | -17.62% |
| Stockout units | 53.92 | 43.10 | -20.05% |
| Average ending inventory | 122.95 | 90.12 | -26.70% |
| Fill rate | 93.88% | 94.21% | +0.32 pp |

These are simulated outcomes under assumed holding, ordering and stockout costs. They are not realized savings or validated retailer economics.

## Policy sensitivity

At a 7-day lead time, moving the service target from 80% to 95% increased base-case simulated cost by 2.28%, reduced stockout units by 13.89%, and improved fill rate by 1.53 pp. Under the 2.5x stockout-penalty scenario, the same policy reduced simulated cost by 4.32% versus the 80% target. At a 21-day lead time, the 95% target reduced stockouts by only 1.21% and increased base-case cost by 2.55%.

This is a trade-off, not a universally optimal service target. The preferred policy depends on lead time and finance-approved cost inputs.

## Reproduce

Configure the private M5 source workflow secrets as described in the README, then run:

```bash
python -m pip install -r requirements-dev.txt
python -m scripts.run_full_population_eda
python -m scripts.prepare_data
python -m scripts.build_features
python -m scripts.train_models
python -m scripts.run_rolling_backtest
python -m scripts.run_forecast_driven_inventory
python -m scripts.run_inventory_sensitivity
python -m pytest -q
```

The exact command list available in a checkout may include additional uncertainty and reporting stages; see the README and `.github/workflows/`.

## Provenance and reconciliation

The canonical detailed results are in [Empirical Evaluation Results](empirical_evaluation_results.md). The separate `reports/tables/business_impact_summary.csv` contains an earlier summary with different totals and percentage changes. Do not combine those numbers with the later final-28-day results unless the generating run, panel, horizon and cost configuration are traced and reconciled. This report intentionally uses only the later documented evaluation table.

## Limitations

- Forecast evaluation covers 200 selected series, not the full M5 population.
- The rolling-origin experiment is one-step-ahead with actual demand becoming available after each date.
- Inventory simulation uses deterministic lead times and assumed costs.
- Sensitivity analysis covers 30 selected series and does not model stochastic supplier delays.
- Empirical conformal coverage is a holdout diagnostic, not a future guarantee.
- No retailer pilot or realized savings are claimed.
