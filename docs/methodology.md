# Methodology

The project uses a chronological train/validation/test split. Baselines include naive, seasonal naive and moving average. Global XGBoost and LightGBM models use lagged demand, rolling statistics, calendar, price and identifiers.

Forecast uncertainty is estimated from out-of-sample validation residuals only. Inventory uses a periodic-review `(R,S)` policy. For an independent daily-demand approximation, protection period is `L + R`, safety stock is `z * sigma_daily * sqrt(L + R)`, and the target inventory position is expected protection-period demand plus safety stock.

Candidate `(R,S)` policies are selected by simulating the 36 service-level/review-period combinations on validation data. The selected policy is then evaluated once on the held-out test period. Baseline and optimized policies share the same simulation dates and series.
