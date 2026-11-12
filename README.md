# Retail Demand Forecasting & Inventory Optimization

An end-to-end applied Data Science project that turns retail point-of-sale history into demand forecasts, uncertainty estimates, replenishment policies, and measurable inventory trade-offs.



**Decision-maker brief:** [Inventory replenishment decision brief](docs/DECISION_BRIEF.md) — summarizes the simulated cost/service improvement, assumptions, and what a real pilot would need.

<p align="left">
  <a href="https://retail-demand-inventory-optimization-v1.streamlit.app/"><strong>Live Streamlit Dashboard</strong></a> ·
  <a href="https://retail-demand-inventory-optimization.onrender.com/"><strong>FastAPI Backend</strong></a> ·
  <a href="https://retail-demand-inventory-optimization.onrender.com/docs"><strong>Interactive API Docs</strong></a> ·
  <a href="https://github.com/Harshithpatali/retail-demand-inventory-optimization/actions"><strong>CI & Experiments</strong></a>
</p>

---

## 1. Problem framing

Retail demand is difficult to plan because sales vary across products, stores, calendar periods, promotions, and seasonal events. Forecast error has operational consequences:

- Under-forecasting can increase stockout exposure and lost sales.
- Over-forecasting can tie up working capital and increase holding costs.
- Intermittent products have many zero-sales days, making standard error metrics and forecasting assumptions less reliable.
- A point forecast alone does not describe the range of plausible demand during a replenishment protection period.

This project addresses the decision chain rather than treating forecasting as an isolated regression task:

1. Understand the full historical demand population.
2. Engineer leakage-aware, time-dependent features.
3. Compare machine-learning forecasts with simple and intermittent-demand baselines.
4. Evaluate forecasts on chronological holdouts and rolling origins.
5. Diagnose uncertainty and empirical interval coverage.
6. Translate forecasts into periodic-review inventory targets.
7. Simulate service, stockout, inventory and cost trade-offs under explicit assumptions.

**Primary analytical question:** can a forecast-informed replenishment policy improve the balance between availability and inventory cost compared with a historical-demand policy on held-out demand?

---

## 2. Dataset and analytical scope

### M5 Forecasting — Accuracy

The M5 dataset contains hierarchical retail unit sales from Walmart stores in the United States. It provides item/store sales history, calendar attributes, and weekly selling prices.

| Data component | Role in the analysis |
|---|---|
| Sales history | Daily unit demand by item and store |
| Calendar | Date, weekday, month, year, week and event/snap-related attributes |
| Sell prices | Item-store-week selling price |
| Product hierarchy | Item, department and category identifiers |
| Store hierarchy | Store and state identifiers |

The full-population EDA reads the original evaluation sales matrix in chunks and covers **30,490 item-store series across 1,941 daily columns**. It does not construct a 30,490-series long-form Parquet panel.

### Two intentionally separate data scopes

| Scope | Population | Purpose |
|---|---:|---|
| Full-population EDA | 30,490 item-store series | Dataset-wide descriptive analysis and segmentation |
| Forecasting and inventory experiments | 200 selected item-store series | Reproducible model development, temporal validation and simulation |

The modelling subset is deterministic: up to 20 high-volume items per store, with a maximum of 200 series, selected using the configured recent-demand ranking. This makes the model experiments practical to reproduce while keeping the EDA population-wide.

The source archive is stored in a **private Supabase Storage bucket**. Raw CSVs and the ZIP are not committed to GitHub.

---

## 3. Full-population exploratory data analysis

The full-data EDA runs on the original sales matrix before the modelling subset is selected. It uses chunked CSV reads and accumulates daily and per-series statistics, avoiding a full long-panel expansion.

### Analysis dimensions

| EDA area | Questions and measures |
|---|---|
| Population profile | Number of series, history length, active/inactive series and total units |
| Demand distribution | Series cumulative demand, average daily demand, standard deviation, maximum daily demand and quantiles |
| Sparsity and intermittency | Zero-demand-day fraction, non-zero selling days and average demand interval |
| Intermittent-demand structure | Average demand interval (ADI) and squared coefficient of variation (CV²) diagnostics |
| Temporal behaviour | Daily aggregate trend, monthly demand, weekday profile and active-series trend |
| Product segmentation | Demand and activity by category and department |
| Store geography | State/store demand aggregates using dataset identifiers |
| Price structure | Sell-price distribution, price changes and store-level price summaries |

### Intermittency diagnostics

For each item-store series, the EDA calculates:

- **Zero-day fraction:** proportion of observed days with zero recorded sales.
- **Average demand interval (ADI):** number of observed days divided by the number of non-zero demand days.
- **Demand CV²:** squared coefficient of variation of daily demand.

ADI and CV² provide a descriptive view of demand sparsity and variability. They are useful for identifying series that may behave differently from smooth, frequently selling products. They are not used as causal explanations.

### EDA outputs

After the full-data workflow succeeds, generated files are committed under [`reports/eda/full_data/`](reports/eda/full_data/):

- `FULL_DATA_EDA.md` — scope, headline statistics and interpretation.
- `full_eda_summary.json` — machine-readable headline summary.
- `series_metrics.csv` — one row per item-store series.
- `daily_demand_full_population.csv` — daily aggregate demand and calendar attributes.
- `monthly_demand.csv` and `weekday_demand.csv` — temporal summaries.
- `by_state_id.csv`, `by_store_id.csv`, `by_cat_id.csv`, `by_dept_id.csv` — segment aggregates.
- `price_summary_by_store.csv` and `price_distribution.csv` — price diagnostics.
- `figures/` — daily trend, monthly and weekday patterns, demand distribution, intermittency, ADI/CV², segment comparisons and price distribution.

The full-population EDA is descriptive. It should not be confused with the 200-series model evaluation results below.

---

## 4. Data engineering and feature construction

### Source ingestion

The `process-m5-source-data` GitHub Actions workflow:

1. Authenticates to private Supabase Storage using repository Actions secrets.
2. Downloads the original compressed archive to the ephemeral runner.
3. Verifies ZIP integrity.
4. Extracts only the preferred sales matrix (`sales_train_evaluation.csv`, or the validation matrix as fallback), `calendar.csv`, and `sell_prices.csv`.
5. Runs full-population EDA on the complete sales matrix.
6. Builds the separate 200-series cleaned and feature panels.
7. Validates generated outputs.
8. Deletes the temporary ZIP and raw CSVs.
9. Commits only compact EDA outputs, validation metadata and processed Parquet datasets.

The workflow does not extract the unused second sales matrix or `sample_submission.csv`. Credentials are never stored in the repository.

### Cleaning and joins

The modelling data pipeline:

- Selects the configured item-store series deterministically.
- Converts the wide sales matrix to a long panel for the selected series.
- Joins daily calendar attributes using the day key.
- Joins item-store weekly selling prices using store, item and week keys.
- Applies a within-series forward/backward fill for missing selling-price observations.
- Enforces typed demand, price, date and categorical columns.
- Sorts observations by series and date before feature generation.

Missing prices filled from nearby observations are a preprocessing convention, not independently verified transaction prices.

### Feature engineering

The feature panel combines:

- Lagged demand features.
- Rolling-window demand summaries.
- Calendar and weekday information.
- Product/store categorical identifiers.
- Selling-price information and derived price context.

All temporal evaluation is chronological. Model features for a forecast date must be based on information available before that date; the rolling one-step evaluation protocol makes this information set explicit.

### Processed data artifacts

| Path | Description |
|---|---|
| `data/interim/cleaned_sales.parquet` | Cleaned long-form panel for the selected modelling series |
| `data/interim/validation_report.json` | Compact validation and data-quality summary |
| `data/processed/forecast_features.parquet` | Model-ready feature panel |
| `reports/eda/full_data/` | Full-population EDA tables, report and figures |

---

## 5. Forecasting methodology

The forecasting workflow evaluates gradient-boosted tree models against simple demand baselines.

### Models and benchmarks

- **XGBoost:** gradient-boosted decision trees for nonlinear relationships across lagged demand, calendar, price and series attributes.
- **LightGBM:** a second gradient-boosting implementation used as a model comparator.
- **Naive:** most recently observed demand.
- **Seasonal naive:** demand from the corresponding weekly seasonal position.
- **Moving average:** trailing seven-day average.
- **Croston SBA:** intermittent-demand benchmark that separately estimates non-zero demand size and inter-demand interval.

Baselines are important: a complex model is useful only if it improves on simple, transparent alternatives under the same information constraints.

### Evaluation design

The project distinguishes three evaluation exercises:

1. **Original chronological validation benchmark:** the initial model comparison on the selected 200-series panel.
2. **Historical fixed-model temporal robustness:** one saved XGBoost model evaluated across four consecutive 28-day windows without retraining between windows.
3. **Expanding-window rolling-origin refit:** XGBoost and LightGBM are independently retrained at each of four origins, with the next 28 days evaluated at each origin.

For the rolling-origin comparison, all models and simple baselines are evaluated as **rolling one-step-ahead forecasts**. Each date is forecast from information available before that date; observed demand is then revealed before forecasting the next date. This avoids comparing machine-learning predictions with a baseline that has a different information set.

### Metrics

- **MAE:** mean absolute error, in units.
- **RMSE:** root mean squared error, which penalizes larger errors more strongly.
- **WAPE:** sum of absolute errors divided by total actual demand, reported as a percentage.

WAPE is useful for aggregate retail demand, but can conceal poor performance on low-volume series. Results should be read alongside series-level and segment-level diagnostics.

---

## 6. Empirical forecasting results

### Expanding-window rolling-origin refit

Four successive 28-day origins; pooled out-of-fold results across 22,400 observations (200 series × 112 test days).

| Model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| **XGBoost (refit per origin)** | **7.074** | **10.960** | **29.11%** |
| LightGBM (refit per origin) | 7.132 | 11.007 | 29.35% |
| Moving average (7-day) | 8.383 | 13.030 | 34.49% |
| Naive | 9.386 | 14.845 | 38.62% |
| Seasonal naive (7-day) | 9.793 | 15.646 | 40.29% |

XGBoost achieved the lowest pooled WAPE in this experiment. Its advantage over LightGBM was modest (0.24 percentage points in pooled WAPE), while the gap against the simple baselines was larger.

### Paired series-cluster bootstrap

Paired item-store series bootstrap comparisons evaluate the mean per-series WAPE difference between XGBoost and each reference method.

| Reference | Mean difference (pp) | 95% percentile interval | Bootstrap two-sided sign probability |
|---|---:|---:|---:|
| LightGBM | -0.347 | [-0.479, -0.200] | 0.001 |
| Moving average | -4.875 | [-5.343, -4.412] | 0.001 |
| Naive | -9.851 | [-10.503, -9.174] | 0.001 |
| Seasonal naive | -12.453 | [-13.487, -11.528] | 0.001 |

Negative differences favour XGBoost. The bootstrap resamples paired item-store series to preserve within-series dependence. The reported probability is a bootstrap sign probability around zero, **not** a paired t-test or randomization test. Inference is limited to this selected 200-series panel.

### Other historical model diagnostics

| Experiment | Result |
|---|---|
| Original validation benchmark | XGBoost WAPE 28.08%; naive baseline WAPE 68.73% |
| Historical fixed-model four-window evaluation | Mean WAPE 28.57%; fold range 28.08%–29.43% |
| Croston SBA final 28-day holdout | XGBoost WAPE 28.68%; Croston SBA WAPE 34.34% |

These results come from distinct evaluation scripts and should not be merged into one leaderboard. See the [detailed empirical results](docs/empirical_evaluation_results.md) and [evaluation protocol](docs/empirical_evaluation_protocol.md).

---

## 7. Forecast uncertainty and conformal diagnostics

A point forecast does not quantify uncertainty over the inventory protection period. The project adds empirical residual-based interval diagnostics.

The uncertainty workflow:

- Uses chronological residuals from prior validation data.
- Estimates finite-sample absolute-residual quantiles.
- Uses per-series calibration when sufficient residual history is available, with pooled fallback otherwise.
- Evaluates empirical coverage and mean interval width on a held-out period.
- Includes block residual calibration for multi-day protection-period demand.

### Held-out interval diagnostics

| Nominal coverage | Empirical coverage | Mean interval width |
|---:|---:|---:|
| 80% | 82.43% | 22.95 units |
| 90% | 92.59% | 32.52 units |
| 95% | 95.91% | 39.52 units |

These are empirical results on one held-out sample. Time-series dependence and non-stationarity mean that classical exchangeability-based conformal guarantees should not be assumed. Coverage should be monitored as data and operating conditions change.

---

## 8. Inventory optimization and decision simulation

Forecasts are translated into periodic-review replenishment targets. The decision layer considers demand during the protection period, which is based on lead time plus review period.

The simulation compares a historical-demand policy with a forecast-informed policy using explicit assumptions for:

- Holding cost.
- Ordering cost.
- Stockout penalty.
- Lead time and review period.
- Target service level.
- Minimum order quantity and maximum order quantity.

The inventory simulator is a controlled experiment, not a production retailer replenishment system. It uses deterministic lead times and does not represent actual purchase orders, reserved inventory, supplier uncertainty or verified warehouse-to-store routes.

### Forecast-driven inventory result

Final 28-day test period; mean per-series simulation metrics across eligible item-store series.

| Metric | Historical baseline | Forecast-driven |
|---|---:|---:|
| Simulated total cost | 299.76 | 246.95 |
| Stockout units | 53.92 | 43.10 |
| Average ending inventory | 122.95 | 90.12 |
| Fill rate | 93.88% | 94.21% |

Under the configured assumptions, the forecast-driven policy produced:

- **17.62% lower simulated total cost**
- **20.05% fewer stockout units**
- **26.70% lower average ending inventory**
- **0.32 percentage-point higher fill rate**

These are simulated outcomes under the repository's cost assumptions. They are **not** realized retailer savings or a financial forecast.

### Sensitivity analysis

The inventory sensitivity experiment evaluates:

- Lead times: 1, 3, 5, 7, 10, 14 and 21 days.
- Service-level targets: 80%, 85%, 90%, 95% and 97%.
- Cost scenarios: base case, lower/higher stockout penalty, higher holding cost and higher ordering cost.
- A deterministic 30-series sample stratified across demand-volume ranks.

At a 7-day lead time, moving from an 80% to 95% service target increased base-case simulated cost by 2.28%, reduced stockout units by 13.89%, and improved fill rate by 1.53 percentage points. Under a 2.5× stockout-penalty scenario, the same policy reduced simulated cost by 4.32%. The preferred service target therefore depends on the relative cost of stockouts and excess inventory.

See [inventory methodology](docs/inventory_methodology.md) and [business assumptions](docs/business_assumptions.md).

---

## 9. Product architecture

The project separates data science, API serving and interactive analytics.

| Layer | Technology | Responsibility |
|---|---|---|
| Data processing | Python, pandas, Parquet | Ingestion, validation, cleaning and feature creation |
| Modelling | XGBoost, LightGBM, scikit-learn | Demand forecasting and baseline comparisons |
| Statistical evaluation | NumPy, pandas, bootstrap procedures | Rolling-origin evaluation, uncertainty and sensitivity |
| API | FastAPI | Forecast, EDA, health and inventory endpoints |
| User interface | Streamlit | Interactive EDA, forecast, inventory and scenario workspaces |
| Automation | GitHub Actions | Tests, data processing and repeatable experiments |
| Source storage | Private Supabase Storage | Original compressed M5 archive |

### Interactive dashboard

The Streamlit application is organized around decision workflows:

- **Overview:** executive demand and inventory indicators.
- **Full EDA:** descriptive statistics, demand quantiles, intermittency, trend, seasonality, distributions and lag autocorrelation.
- **Demand Forecast:** model-driven demand projections and uncertainty views.
- **Inventory Control:** replenishment policy and order quantity analysis.
- **Network Intelligence:** state-level demand aggregation and explicitly labelled illustrative distribution-centre scenarios.
- **Business Impact:** service and cost outcomes under stated assumptions.
- **Scenario Studio:** interactive what-if analysis.

### API

The FastAPI service provides endpoints for health checks, EDA, forecasting and inventory decision support. Interactive endpoint documentation is available at the hosted API docs link above.

---

## 10. Reproducibility

### Run locally

Python 3.11 is used in the GitHub Actions data-processing workflow.

Install dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Place the three required M5 source CSVs in `data/raw/`:

- `sales_train_evaluation.csv` (preferred) or `sales_train_validation.csv`
- `calendar.csv`
- `sell_prices.csv`

Run the full-population EDA and modelling pipeline:

```bash
python -m scripts.run_full_population_eda
python -m scripts.prepare_data
python -m scripts.build_features
```

Run model and decision experiments after the processed modelling panel is created:

```bash
python -m scripts.train_models
python -m scripts.estimate_uncertainty
python -m scripts.run_inventory_simulation
python -m scripts.run_rolling_backtest
python -m scripts.run_advanced_evaluation
python -m scripts.run_forecast_driven_inventory
python -m scripts.run_inventory_sensitivity
python -m scripts.build_business_impact
pytest -q
```

### Rebuild from private Supabase source

Configure these repository secrets under **Settings → Secrets and variables → Actions**:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY` (or the supported legacy `SUPABASE_SERVICE_ROLE_KEY`)

Optional: `M5_ZIP_PATH` if the private bucket contains more than one ZIP. The bucket defaults to `m5-raw-data`.

Run the [process M5 source data workflow](.github/workflows/process-m5-source-data.yml) manually from the Actions tab. The workflow downloads the private archive, performs full-population EDA, rebuilds the selected modelling Parquet files, removes temporary raw inputs, and commits only processed outputs. Do not place credentials in source files or commit the raw archive.

### Tests and continuous integration

The repository includes automated tests for data/forecasting components and a GitHub Actions test workflow. The data-processing workflow and empirical-evaluation workflow are separately runnable so data ingestion, model evaluation and code tests can be inspected independently.

---

## 11. Repository map

```text
.
├── api/                         # FastAPI application and route handlers
├── app/                         # Streamlit dashboard
├── configs/                     # Data, model and inventory configuration
├── data/
│   ├── interim/                 # Cleaned selected-series panel and validation
│   └── processed/               # Model-ready feature panel
├── docs/                        # Statistical, inventory and data-policy docs
├── reports/
│   ├── eda/full_data/            # Full-population EDA outputs
│   ├── figures/                  # Experiment figures
│   └── tables/                   # Evaluation tables
├── scripts/                     # Reproducible analysis and experiment entrypoints
├── src/
│   ├── data/                     # Loaders, validation and cleaning
│   ├── features/                 # Feature engineering
│   ├── forecasting/              # Forecasting and baseline logic
│   ├── inventory/                # Replenishment and simulation
│   └── utils/                    # Configuration and shared utilities
└── tests/                        # Automated tests
```

---

## 12. Limitations and responsible interpretation

- Full-population descriptive analysis covers 30,490 series, but the main forecasting and inventory experiments cover 200 selected series.
- Results on the selected high-volume panel do not establish performance on the complete M5 population.
- WAPE is an aggregate metric and can hide weak performance on low-volume or intermittent series.
- Rolling one-step-ahead evaluation is not equivalent to a fixed-origin multi-week forecast.
- Conformal coverage is empirical on a holdout, not a guarantee under serial dependence or distribution shift.
- Inventory costs are assumptions, not retailer-provided or realized economics.
- The inventory sensitivity analysis uses 30 series; it is not a complete assortment-wide policy optimization.
- Lead times are deterministic. Stochastic supplier delays and replenishment disruptions are future extensions.
- M5 includes store/state identifiers but not verified store coordinates, warehouse locations, or actual store-to-warehouse assignments. Map layers using illustrative hubs are scenario visualizations, not observed logistics networks.
- Future prices, promotions and event information are not always known at forecast time. Live recursive forecasts use conservative assumptions for unavailable future inputs.
- The live inventory position does not currently reconcile open purchase orders and reserved stock.

---

## 13. Further research

Potential next steps include:

- Evaluate all 30,490 series with scalable distributed feature processing and segment-aware model selection.
- Add hierarchical forecasting and coherent aggregation across item, department, category, store and state levels.
- Compare global models with local and intermittent-demand specialists by demand segment.
- Add probabilistic forecasting and rolling coverage monitoring under temporal dependence.
- Extend the inventory simulator with stochastic lead times, order pipelines, service constraints and realistic review calendars.
- Evaluate policy robustness under demand shocks, promotions and price changes.
- Add operational monitoring for data drift, forecast bias, service levels and realized replenishment outcomes.

---

## 14. References

- Makridakis, S., Spiliotis, E., & Assimakopoulos, V. — M5 accuracy forecasting competition and dataset.
- [M5 Forecasting — Accuracy on Kaggle](https://www.kaggle.com/competitions/m5-forecasting-accuracy)
- [XGBoost documentation](https://xgboost.readthedocs.io/)
- [LightGBM documentation](https://lightgbm.readthedocs.io/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Streamlit documentation](https://docs.streamlit.io/)

---

## Project status

The GitHub code, data-processing workflow and automated test workflow have completed successfully. The full-population EDA job processed all **30,490 series × 1,941 daily columns** from the original M5 evaluation matrix. The source-processing run is available [here](https://github.com/Harshithpatali/retail-demand-inventory-optimization/actions/runs/43025180207).

**Important:** EDA generation succeeded in the workflow. The workflow's commit step initially reported a clean working tree, so the EDA report files were not yet confirmed in GitHub at that run. A follow-up workflow change explicitly stages those outputs; check the latest Actions run before relying on the report links.
