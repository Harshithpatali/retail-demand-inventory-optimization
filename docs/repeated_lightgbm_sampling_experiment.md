# Repeated LightGBM sampling experiment

This branch adds an isolated experiment: 20 independent LightGBM fits, each trained on exactly 200,000 rows sampled without replacement from eligible historical training origins.

## Design
- Four historical training origins, one fixed chronological validation origin, and one untouched chronological test origin are reused from the existing full-population pipeline.
- Sampling is proportional within strata defined by store, category, forecast horizon, and demand pattern (regular, lumpy, intermittent). Demand pattern is derived from historical zero-fraction features.
- Seeds are fixed and distinct (20261125 through 20261144). Hyperparameters and features stay fixed to isolate sampling/seed variability.
- A run fails if 200,000 eligible rows are unavailable; it never silently reduces sample size.
- Selection uses validation WAPE + 0.15 × absolute aggregate bias. This is a declared heuristic; WAPE and bias must also be reviewed separately.
- The selected validation winner is evaluated once on the fixed test origin.

## Safety and promotion
The candidate is written to models/full_population/candidates/repeated_200k_lightgbm_candidate.txt. The active model path models/full_population/m5_global_lightgbm_28d.txt is never written. The existing FastAPI routes, prediction contract, Render deployment, Streamlit app, R2 publisher, and production workflow are unchanged. Candidate reports and model are attached to the GitHub Actions run for 30 days.

Promotion requires a separate manual review: compare candidate and active model on identical windows, verify feature/category encodings and prediction parity, and test the existing API. No automatic deployment or model replacement occurs.

## Run
From the experiment branch, manually trigger the repeated-lightgbm-sampling-experiments GitHub Actions workflow. It uses the existing Supabase Actions secrets to retrieve the private M5 archive and adds no new secrets.
