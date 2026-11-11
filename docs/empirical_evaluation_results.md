# Empirical Evaluation Results

**Evaluation run:** [GitHub Actions run 42961846997](https://github.com/Harshithpatali/retail-demand-inventory-optimization/actions/runs/42961846997)  
**Result:** All four experiment stages completed successfully.  
**Dataset:** 388,200 daily observations, 200 item-store series, 2011-01-29 through 2016-05-22.  
**Evaluation artifact:** [Download CSV result tables](https://github.com/Harshithpatali/retail-demand-inventory-optimization/actions/runs/42961846997/artifacts/13829267285)

## 1. Chronological forecast robustness

The saved XGBoost model was evaluated on four consecutive 28-day windows. The model was held fixed across windows; it was not retrained at each origin.

| Fold | Test window | MAE | RMSE | WAPE |
|---:|---|---:|---:|---:|
| 1 | 2016-02-01 to 2016-02-28 | 7.025 | 10.855 | 28.09% |
| 2 | 2016-02-29 to 2016-03-27 | 7.039 | 10.556 | 29.43% |
| 3 | 2016-03-28 to 2016-04-24 | 6.836 | 10.169 | 28.08% |
| 4 | 2016-04-25 to 2016-05-22 | 6.869 | 10.552 | 28.68% |

Mean WAPE across folds: **28.57%**. Fold range: **28.08%–29.43%**. This indicates relatively stable performance over these four adjacent windows, not a guarantee under future distribution shift.

## 2. Intermittent-demand baseline comparison

On the final 28-day holdout, rolling one-step XGBoost predictions were compared with rolling one-step Croston SBA predictions. Both use information available before each prediction date.

| Model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| XGBoost | 6.869 | 10.552 | 28.68% |
| Croston SBA | 8.224 | 12.506 | 34.34% |

XGBoost WAPE was **16.48% lower** than Croston SBA on this holdout. Croston SBA remains a useful benchmark for intermittent series; the aggregate comparison does not imply XGBoost wins for every SKU.

## 3. Conformal interval diagnostics

Intervals were calibrated using prior chronological validation residuals and evaluated on 5,600 held-out observations. Per-series calibration was used where at least eight residuals were available, with pooled residuals as a fallback.

| Nominal coverage | Empirical coverage | Mean interval width (units) |
|---:|---:|---:|
| 80% | 82.43% | 22.95 |
| 90% | 92.59% | 32.52 |
| 95% | 95.91% | 39.52 |

Coverage is empirical on this one holdout. Time-series dependence and non-stationarity mean classical exchangeability-based conformal guarantees should not be assumed.

## 4. Forecast-driven inventory evaluation

On the final 28-day test period, the validation-selected forecast-driven policy was compared with a historical-demand baseline. Reported values below are mean per-series simulation metrics across eligible item-store series.

| Metric | Historical baseline | Forecast-driven |
|---|---:|---:|
| Simulated total cost | 299.76 | 246.95 |
| Stockout units | 53.92 | 43.10 |
| Average ending inventory | 122.95 | 90.12 |
| Fill rate | 93.88% | 94.21% |

Relative changes: simulated cost **-17.62%**, stockout units **-20.05%**, average inventory **-26.70%**, fill rate **+0.32 percentage points**.

These are outcomes under the repository's explicit holding, ordering and stockout cost assumptions. They are not realized retailer savings. The 28-day validation period is split between residual calibration and policy selection before the policy is frozen for test evaluation. The forecast is rolling one-step-ahead, not a fixed-origin multi-week plan.

## 5. Inventory policy sensitivity

The sensitivity analysis uses 30 deterministic item-store series sampled across training-volume ranks and a 28-day holdout. It evaluates lead times of **1, 3, 5, 7, 10, 14 and 21 days**, service-level targets of **80%, 85%, 90%, 95% and 97%**, and five cost scenarios (base, 0.5x stockout penalty, 2.5x stockout penalty, 2x holding cost, and 2x ordering cost). Lead times are capped so an order can arrive within the test window.

Illustrative base-cost results at a 7-day lead time:

| Target service level | Cost change vs 80% | Stockout-unit change | Fill-rate change |
|---:|---:|---:|---:|
| 80% | 0.00% | 0.00% | 0.00 pp |
| 90% | +0.67% | -8.96% | +0.98 pp |
| 95% | +2.28% | -13.89% | +1.53 pp |

Under the 2.5x stockout-penalty scenario, the 95% target at a 7-day lead time reduced simulated cost by **4.32%** versus the 80% target, while reducing stockout units by **13.89%** and improving fill rate by **1.53 pp**. This illustrates how the preferred policy depends on the relative economics of holding inventory versus stockouts.

At a 21-day lead time, the same 95% target reduced stockout units by only **1.21%** while increasing base-case simulated cost by **2.55%**. Long replenishment delays materially limit the benefit of raising the target in a short 28-day test window.

## 6. Reproducibility and data geography

All result tables are uploaded by the evaluation workflow as a 30-day GitHub Actions artifact. The workflow can be rerun from the Actions tab.

M5 store IDs and state codes are observed dataset fields. M5 does not contain verified store street addresses, store coordinates, warehouse coordinates or actual store-to-warehouse assignments. State-level store performance is therefore shown as a state aggregation. Distribution-centre markers and state-based assignments are explicitly synthetic planning scenarios, not real facilities or observed logistics links. See [network geography and data policy](network_intelligence_data_policy.md).

## Limitations to state in a CV or interview

- Only 200 item-store series are evaluated, not the complete 30,490-series M5 panel.
- Rolling-origin metrics use one fixed model across four windows; no per-origin retraining was performed.
- Conformal coverage is a single-holdout empirical diagnostic, not a guaranteed future coverage rate.
- Forecast-driven inventory is a 28-day rolling one-step decision simulation.
- Sensitivity results use 30 representative series and assumed cost multipliers.
- Lead times are deterministic; stochastic supplier delays and real warehouse/store geometry are not modeled.
- Simulated savings are not realized commercial savings.
