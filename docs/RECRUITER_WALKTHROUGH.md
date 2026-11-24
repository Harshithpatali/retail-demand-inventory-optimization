# Recruiter walkthrough (2–3 minutes)

## 0:00–0:25 — Business problem

“This project explores retail demand forecasting and inventory replenishment using Walmart's M5 dataset. The business problem is a trade-off: under-forecasting can contribute to stockouts, while over-forecasting can increase holding costs. Intermittent products make the problem harder because many item-store days have zero recorded sales.”

## 0:25–0:55 — Data and architecture

“I built two separate analytical tracks. First, I processed the complete dataset: 30,490 item-store series across 1,941 daily observations. The full-population EDA runs in chunks. Second, I used a deterministic 200-series panel for more detailed rolling-origin model comparisons and inventory simulation. GitHub Actions automates processing; Cloudflare R2 stores Parquet artifacts; Supabase holds curated SQL analytics; FastAPI serves the data and Streamlit provides the dashboard.”

## 0:55–1:35 — Forecasting and evaluation

“For the full-population forecast, I created lag, rolling, calendar and intermittency features and compared nested training samples of 25%, 50%, 75% and 100%. I selected the 75% sample using a validation score combining WAPE and an aggregate-bias penalty, then evaluated once on an untouched test origin. It achieved 72.50% WAPE versus 86.27% for seasonal naive. This is a 15.95% relative WAPE reduction, but the absolute error remains high and the model under-forecast by about 4.81%.”

“For the separate 200-series rolling-origin experiment, XGBoost achieved 29.11% WAPE, slightly ahead of LightGBM at 29.35%. I keep these results separate because they use a different population and evaluation design.”

## 1:35–2:10 — Inventory decision layer

“I then translated forecasts into a periodic-review target over lead time plus review period. The forecast policy adds empirical block-conformal safety stock. I compared it with a historical-demand policy on held-out demand. Under the configured assumptions, simulated total cost was 17.62% lower and stockout units were 20.05% lower. These are simulated results, not real retailer savings. The cost values are explicit assumptions, and lead times are deterministic.”

## 2:10–2:40 — Limitations and next step

“The key limitations are intermittent demand, high full-population WAPE, missing future price and event information, and the absence of true inventory positions, purchase orders and supplier uncertainty. The next step for a real business would be a shadow evaluation using retailer inventory and supplier data, with finance-approved cost parameters.”

## Suggested live demo order

1. Open the [Streamlit dashboard](https://retail-demand-inventory-optimization-v1.streamlit.app/).
2. Show **Full Population Forecast** and explain the 30,490-series scope and test baseline comparison.
3. Show the **Demand Forecast** workspace and explain the separate 200-series evaluation track.
4. Show **Inventory Control** and point out lead time, review period, service level and order quantity assumptions.
5. Close with the limitations and the decision brief.

## Questions to be ready for

- **Why is full-population WAPE so high?** The population includes many intermittent series; aggregate errors are affected by zero-heavy and bursty demand, and future price/event inputs are unavailable.
- **Why are there two WAPE figures?** The 72.50% result is the full 30,490-series global LightGBM experiment. The 29.11% result is a different XGBoost experiment on a selected 200-series panel.
- **Are the savings real?** No. They are historical simulation outputs under assumed holding, ordering and stockout penalties.
- **What would be needed for production?** Real inventory positions, purchase orders, reservations, supplier lead-time distributions, pack-size constraints, future price/promotion data, and finance-approved cost inputs.
