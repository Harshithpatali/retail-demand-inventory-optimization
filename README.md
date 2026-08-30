# Retail Demand Forecasting & Inventory Optimization System

A portfolio-grade, CPU-friendly end-to-end Data Science / ML Engineering project built around the M5 Forecasting — Accuracy dataset.

## What this project demonstrates

Business framing, intermittent-demand EDA, feature engineering, time-series validation, strong baselines, XGBoost, LightGBM, out-of-sample uncertainty, periodic-review `(R,S)` inventory optimization, simulation, cost analysis, sensitivity analysis, FastAPI, Streamlit, automated tests, and Render readiness.

## Hardware-conscious design

The default pipeline does **not** melt all 30,490 M5 series into a huge modeling table. It deterministically selects the highest-demand series, up to 20 items per store and 200 total series. Change this through `configs/data_config.yaml`.

## 1. Raw-data placement

Put all five M5 files in `data/raw/`:

```text
sales_train_evaluation.csv
sales_train_validation.csv
calendar.csv
sell_prices.csv
sample_submission.csv
```

The pipeline validates their presence and reports clear missing-file errors.

## 2. Environment

On Windows PowerShell, from the project root:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Test the codebase

```powershell
pytest -q
```

## 4. Run the full pipeline

```powershell
python -m scripts.prepare_data
python -m scripts.build_features
python -m scripts.train_models
python -m scripts.estimate_uncertainty
python -m scripts.run_inventory_simulation
python -m scripts.build_business_impact
pytest -q
```

## 5. Notebook order

Run notebooks `01` through `17` in numerical order after the relevant artifacts have been generated. The notebooks are analysis-first: they contain their own EDA, diagnostic plots, tables, experiments and interpretations, while reusable production logic remains under `src/`.

## 6. Forecasting methodology

The forecasting experiment compares naive, seasonal naive, moving average, XGBoost and LightGBM. The primary ML selection metric is validation WAPE. MAE and RMSE remain secondary diagnostics.

## 7. Uncertainty

Residual uncertainty is calculated from validation-period predictions made by a model trained only on the training period. The final model artifact is then refit on train+validation for future forecasting. This prevents in-sample residual leakage.

## 8. Inventory methodology

The final inventory layer uses a genuine periodic-review `(R,S)` policy:

```text
R = review period
S = target inventory position
Protection period = lead time + review period
Safety stock = z * sigma_daily * sqrt(protection period)
```

At each review date, inventory position is checked. Outstanding orders count toward inventory position. Orders arrive only after lead time. Candidate policies are optimized on validation total cost and evaluated on the same held-out test dates.

## 9. API

Start FastAPI:

```powershell
uvicorn api.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

Endpoints:

```text
GET  /health
POST /forecast
POST /inventory
POST /scenario
GET  /business
GET  /options
```

## 10. Streamlit

In another terminal:

```powershell
streamlit run dashboard/app.py
```

Open `http://localhost:8501`.

The dashboard uses HTTP correctly: GET requests use `httpx.get(...)`; POST requests send JSON with `httpx.post(..., json=payload)`.

Set `API_BASE_URL` for hosted environments. Local default is `http://localhost:8000`.

## 11. Outputs

Key artifacts include:

```text
data/interim/cleaned_sales.parquet
data/processed/forecast_features.parquet
data/processed/inventory_simulation.parquet
data/processed/optimized_policies.parquet
models/forecasting/xgboost.joblib
models/forecasting/lightgbm.joblib
models/forecasting/best_model.joblib
models/forecasting/validation_model.joblib
models/uncertainty/residual_stats.joblib
models/uncertainty/business_metrics.joblib
reports/tables/model_comparison_validation.csv
reports/tables/business_impact_summary.csv
```

## 12. Business-impact interpretation

The project never fabricates savings. `change_pct` is always calculated as:

```text
(optimized - baseline) / baseline * 100
```

For costs and stockouts, a negative change is better. For service/fill rate, a positive change is better. Simulation results are labeled as simulation results under explicit assumptions.

## 13. Render

`render.yaml` contains native Python service definitions for FastAPI and Streamlit. No Dockerfile is required.

## 14. Important limitations

The default experiment is a portfolio-scale subset rather than the full M5 panel. Future price/event information may not be known in real deployment, so the API uses available processed context and conservative defaults/carry-forward behavior. Inventory costs are assumptions, not actual retailer economics.


### Inventory policy assumptions

Inventory demand statistics use a configurable 365-day training window by default. The inventory policy is a genuine periodic-review `(R,S)` policy: reviews occur every R days, protection period is lead time plus review period, and a configurable 5-unit minimum order quantity is used as a simulation assumption.
