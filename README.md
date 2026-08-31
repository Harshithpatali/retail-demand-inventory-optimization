# Retail Demand Forecasting & Inventory Optimization System

A portfolio-grade, CPU-friendly end-to-end Data Science / ML Engineering project built around the M5 Forecasting — Accuracy dataset.

**Live dashboard:** https://retail-demand-inventory-optimization-v1.streamlit.app/

**Live FastAPI backend:** https://retail-demand-inventory-optimization.onrender.com/

## Project Overview

This project combines demand forecasting with inventory optimization to answer a practical retail question:

> **How can better demand forecasts and cost-aware inventory policies reduce total inventory cost while maintaining service levels?**

The project covers the complete workflow:

```text
Raw retail data
      ↓
Data validation & preparation
      ↓
Exploratory demand analysis
      ↓
Feature engineering
      ↓
Time-based validation
      ↓
Baseline forecasting
      ↓
XGBoost / LightGBM
      ↓
Out-of-sample uncertainty
      ↓
Periodic-review (R,S) inventory optimization
      ↓
Inventory simulation
      ↓
Business-impact analysis
      ↓
FastAPI
      ↓
Streamlit dashboard
```

## Key Dataset Findings

The initial data investigation showed strongly intermittent and heterogeneous retail demand:

| Metric | Result |
|---|---:|
| Historical units | ~65.70 million |
| Mean demand per item-store-day | 1.13 |
| Overall zero-demand rate | 68.20% |
| Median series zero-demand rate | 73.55% |
| Completely zero series | 0 |
| Maximum single-day demand | 763 units |
| Total candidate series | 30,490 |
| Working modeling subset | 200 series |
| Prepared feature rows | 388,200 |

The demand distribution is highly skewed and intermittent, so model evaluation uses **WAPE as the primary metric**, with MAE and RMSE as secondary diagnostics.

Demand is also highly concentrated: a relatively small number of item-store series account for a large share of total demand. This motivates both global forecasting and segment-level evaluation.

## Modeling Strategy

The forecasting experiment compares:

1. Naive baseline
2. Seasonal Naive (7-day)
3. Moving Average
4. XGBoost
5. LightGBM

The central modeling principle is:

> **A machine-learning model should beat a strong forecasting baseline before it is considered useful.**

The final selected model is **XGBoost**.

### Validation Results

| Model | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| **XGBoost** | **6.836** | **10.169** | **0.2808** |
| LightGBM | 6.895 | 10.309 | 0.2832 |
| Moving Average | 9.862 | 14.499 | 0.4051 |
| Seasonal Naive | 11.058 | 16.505 | 0.4542 |
| Naive | 16.732 | 24.879 | 0.6873 |

XGBoost achieved the best validation WAPE, MAE, and RMSE in the implemented experiment.

## Uncertainty Estimation

Residual uncertainty is estimated from **out-of-sample validation predictions**, rather than in-sample training residuals.

Current validation-period uncertainty summary:

```text
n       = 5,600
MAE     = 6.836
RMSE    = 10.169
WAPE    = 0.2808
Period  = 2016-03-28 to 2016-04-24
```

Prediction intervals are built around the forecast using the estimated residual standard deviation.

## Inventory Optimization

The final inventory layer uses a genuine **periodic-review (R,S) policy**.

At each review point:

```text
Inventory position
    = on-hand inventory
    + outstanding purchase orders

If inventory position < S:
    place order to restore the target position
```

The protection period is:

```text
Protection period = lead time + review period
```

Safety stock is based on service level and demand uncertainty over that protection period.

Candidate policies are selected using **validation total cost**:

```text
Total Cost
= Holding Cost
+ Ordering Cost
+ Stockout Cost
```

The final test period is held out and evaluated only after the policy is selected on validation data.

### Inventory Assumptions

The deployed experiment uses:

```text
Default service level:      90%
Default lead time:          7 days
Default review period:      7 days
Minimum order quantity:     5 units
Maximum order quantity:     500 units
Holding cost:               0.05 / unit / day
Ordering cost:              5.00 / order
Stockout cost:              2.00 / unit
Demand estimation window:  365 days
```

These are modeling assumptions rather than actual retailer economics.

## Business Impact Results

The optimized policy was evaluated on the **same held-out test period** as the baseline policy.

| Metric | Baseline | Optimized | Change |
|---|---:|---:|---:|
| Total cost | 59,951.45 | **50,230.82** | **-16.21%** |
| Holding cost | 34,425.33 | **26,374.01** | **-23.39%** |
| Ordering cost | 3,960.00 | 8,900.00 | +124.75% |
| Stockout cost | 21,566.12 | **14,956.81** | **-30.65%** |
| Average inventory | 122.95 | **94.19** | **-23.39%** |
| Stockout units | 10,783.06 | **7,478.41** | **-30.65%** |
| Stockout days | 390 | **342** | **-12.31%** |
| Service level | 91.96% | **94.42%** | **+2.46 pp** |
| Orders | 792 | 1,780 | +124.75% |

The optimized policy reduced simulated total cost by **16.21%** while also increasing simulated service level by **2.46 percentage points** and reducing stockout units by **30.65%**.

The increase in ordering cost is explicitly reported rather than hidden: the optimization trades more frequent replenishment for lower holding and stockout costs.

## Dashboard

The deployed Streamlit dashboard provides five interactive views:

- **Executive Overview** — portfolio-level KPIs and business impact.
- **Demand Forecast** — forecast horizon, prediction intervals, model information, and forecast table.
- **Inventory Recommendation** — reorder decision, safety stock, reorder point, lead-time demand, and order quantity.
- **Business Impact** — baseline versus optimized cost, inventory, stockout, and service metrics.
- **Scenario Analysis** — stress testing under hypothetical demand growth.

The dashboard uses the FastAPI backend through `API_BASE_URL`; it does not train models or process the raw M5 dataset in the frontend.

### Dashboard Screenshots

#### Executive Overview

![Executive Overview](docs/screenshots/executive_overview.png)

#### Business Impact

![Business Impact](docs/screenshots/business_impact.png)

#### Inventory Recommendation

![Inventory Recommendation](docs/screenshots/inventory_recommendation.png)

#### Scenario Analysis

![Scenario Analysis](docs/screenshots/scenario_analysis.png)

> The screenshot files should be stored in `docs/screenshots/` using the filenames shown above.

## Deployment Architecture

```text
                         GitHub
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        Render Web Service       Streamlit Cloud
              │                         │
           FastAPI API                 │
              │                         │
              └────────── HTTP ────────┘
```

### FastAPI

The API exposes:

```text
GET  /health
GET  /options
GET  /business
POST /forecast
POST /inventory
POST /scenario
```

The production API is hosted on Render.

### Streamlit

The interactive dashboard is hosted on Streamlit Community Cloud.

Production configuration:

```text
API_BASE_URL=https://retail-demand-inventory-optimization.onrender.com
```

## Hardware-Conscious Design

The full M5 dataset is much larger than required for an interactive portfolio deployment. The default modeling pipeline therefore selects a deterministic subset of high-demand item-store series rather than melting all 30,490 series into one large modeling table.

The default selection is controlled through:

```text
configs/data_config.yaml
```

Current default experiment:

```text
Up to 20 items per store
Up to 200 total series
388,200 prepared feature rows
```

Raw M5 data remains local and is intentionally excluded from GitHub.

## Raw Data Placement

Place the original M5 files under:

```text
data/raw/
```

Expected files:

```text
sales_train_evaluation.csv
sales_train_validation.csv
calendar.csv
sell_prices.csv
sample_submission.csv
```

The pipeline validates the expected files before processing.

## Environment Setup

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For notebook development and the complete data-science environment:

```powershell
python -m pip install -r requirements-dev.txt
```

## Run Tests

```powershell
pytest -q
```

The test suite covers data validation, transformations, feature engineering, forecasting baselines, inventory calculations, and periodic-review simulation behavior.

## Run the Full Local Pipeline

```powershell
python -m scripts.prepare_data
python -m scripts.build_features
python -m scripts.train_models
python -m scripts.estimate_uncertainty
python -m scripts.run_inventory_simulation
python -m scripts.build_business_impact
pytest -q
```

## Generate Deployment Artifacts

The deployed API uses processed artifacts and trained model files rather than the raw dataset.

Important artifacts include:

```text
data/processed/forecast_features.parquet
data/processed/inventory_simulation.parquet
data/processed/optimized_policies.parquet
data/processed/series_options.json

models/forecasting/best_model.joblib
models/forecasting/xgboost.joblib
models/forecasting/validation_model.joblib
models/uncertainty/residual_stats.joblib
models/uncertainty/business_metrics.joblib
```

The raw dataset under `data/raw/` is intentionally not committed because of its size.

## Notebook Workflow

The project contains 17 notebooks, intended to be run in numerical order:

```text
01  Business Problem & Data Understanding
02  Data Ingestion & Validation
03  Data Cleaning & Preparation
04  Exploratory Data Analysis
05  Demand Pattern Analysis
06  Feature Engineering
07  Time-Based Split
08  Baseline Forecasting
09  XGBoost Forecasting
10  LightGBM Forecasting
11  Forecasting Model Comparison
12  Demand Uncertainty
13  Inventory Optimization
14  Inventory Simulation
15  Business Impact Analysis
16  Sensitivity Analysis
17  Final Analysis & Recommendations
```

The notebooks are intended to be **analysis-first and interactive**, with detailed visualizations, diagnostics, experiments, tables, and interpretations. Reusable production logic remains under `src/`.

## Repository Structure

```text
retail-demand-inventory-optimization/
│
├── api/
│   ├── main.py
│   ├── routes/
│   ├── schemas/
│   └── services/
│
├── configs/
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── docs/
│   ├── architecture.md
│   ├── business_assumptions.md
│   ├── data_dictionary.md
│   ├── inventory_methodology.md
│   ├── methodology.md
│   └── model_card.md
│
├── models/
│
├── notebooks/
│
├── reports/
│   ├── figures/
│   └── tables/
│
├── scripts/
│
├── src/
│   ├── business/
│   ├── data/
│   ├── features/
│   ├── forecasting/
│   ├── inventory/
│   ├── simulation/
│   ├── uncertainty/
│   └── utils/
│
└── tests/
```

## Important Limitations

- The default experiment is a portfolio-scale subset rather than the full M5 panel.
- Forecasting uses processed historical context and conservative assumptions for future price/event information.
- The deployed API serves pre-trained artifacts; retraining is performed locally.
- Inventory costs and MOQ are explicit assumptions and should be replaced with retailer-specific economics for real operational use.
- Simulated service levels and cost savings are experiment results, not guarantees of future savings.

## Reproducibility Principle

The project separates experimentation from deployment:

```text
Local machine
    ↓
Train / validate / optimize
    ↓
Persist artifacts
    ↓
Deploy inference API
    ↓
Interactive dashboard
```

This keeps the deployed service small and predictable while preserving the full data-science workflow in the repository.

## License

See `LICENSE`.