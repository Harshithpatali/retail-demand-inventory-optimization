# Retail Demand Forecasting & Inventory Optimization System

An end-to-end Data Science project using the M5 Forecasting — Accuracy dataset to connect demand forecasting, uncertainty estimation, and inventory decisions.

**Live products:** [Streamlit dashboard](https://retail-demand-inventory-optimization-v1.streamlit.app/) · [FastAPI service](https://retail-demand-inventory-optimization.onrender.com/) · [API docs](https://retail-demand-inventory-optimization.onrender.com/)

## Core workflow

Raw M5 data → validation and EDA → lag/rolling/calendar/price features → baseline and gradient-boosted forecasting → out-of-sample uncertainty calibration → periodic-review inventory policy → event-driven simulation → business impact.

The default experiment uses a deterministic 200 item–store subset from the 30,490 candidate M5 series. Financial costs are transparent simulation assumptions, not retailer-provided economics.

## Reported original experiment

The original validation benchmark reported XGBoost WAPE of 0.2808, compared with 0.6873 for the naive baseline. The original inventory simulation reported a 16.21% reduction in simulated cost, with a 2.46 percentage-point increase in unit fill/service ratio. These are historical results from the original experiment and are not re-labelled as outcomes of the new advanced evaluation scripts.

## Interactive analytics dashboard

The Streamlit workspace includes an executive overview, full-history EDA, interactive demand forecast, inventory control, business-impact analysis, and a what-if scenario studio. The EDA page exposes descriptive statistics, demand quantiles, intermittency, long-run trend, monthly and weekday seasonality, distribution, and lag autocorrelation. The API caches full-series EDA results with a bounded process-local cache.

## Advanced statistical evaluation

Additional analysis tools are available:

| Command | Purpose |
|---|---|
| `python -m scripts.run_rolling_backtest` | Multiple chronological forecast origins |
| `python -m scripts.run_advanced_evaluation` | Croston SBA comparison and empirical interval coverage/width |
| `python -m scripts.run_forecast_driven_inventory` | Validation-selected forecast-informed inventory policies evaluated on held-out demand |

New components include finite-sample conformal residual quantiles, block residual calibration over protection periods, Croston/SBA intermittent-demand baselines, and forecast-driven (R,S) targets.

See [advanced statistical methodology](docs/advanced_statistical_methodology.md), [inventory methodology](docs/inventory_methodology.md), and [business assumptions](docs/business_assumptions.md).

## Reproduce

Download the M5 Forecasting — Accuracy files and place them in `data/raw/`, then install dependencies:

```bash
python -m pip install -r requirements-dev.txt pytest
python -m scripts.prepare_data
python -m scripts.build_features
python -m scripts.train_models
python -m scripts.estimate_uncertainty
python -m scripts.run_inventory_simulation
python -m scripts.run_rolling_backtest
python -m scripts.run_advanced_evaluation
python -m scripts.run_forecast_driven_inventory
python -m scripts.build_business_impact
pytest -q
```

Raw data and generated artifacts are intentionally not committed. See the configuration files for the subset size, split windows, inventory costs, lead time, review periods, MOQ, and maximum order quantity.

## Important limitations

- The standard model experiment uses 200 series, not the complete M5 panel.
- Future promotions, prices, and event signals are not fully known; the live recursive API forecast uses conservative defaults.
- Conformal coverage under serial dependence is empirical and must be monitored over time.
- The forecast-driven inventory evaluation is a rolling one-step-ahead decision simulation, not a fixed-origin multi-week forecast.
- Lead time is deterministic in the current simulator; stochastic supplier delays remain a future extension.
- All reported inventory economics are simulated under assumptions and are not evidence of realized retailer savings.
