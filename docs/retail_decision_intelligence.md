# Retail Decision Intelligence: Supabase analytics layer

## Data ownership
- Original `m5-forecasting-accuracy.zip` remains in private Supabase Storage bucket `m5-raw-data`.
- PostgreSQL stores only the curated item-store-day panel from `data/interim/cleaned_sales.parquet`, plus small dimension and decision tables.
- Model files and full Parquet artifacts remain in the repository/build artifacts; they are not copied into Postgres.

## Schema
The private `retail` schema contains:
- `dataset_runs`: immutable load metadata and source provenance.
- `dim_product`, `dim_store`, `dim_date`: compact dimensions.
- `fact_daily_demand`: one row per dataset run, store, item and date.
- `model_evaluation`: rolling-origin metrics by model, fold and demand segment.
- `forecast_runs`, `forecast_predictions`: optional persisted forecast vintages and intervals.
- `inventory_scenarios`: explicit scenario assumptions and recommendations; not observed inventory.

Views:
- `v_product_store_performance`
- `v_demand_seasonality`
- `v_inventory_demand_profile`

The schema is private, RLS is enabled on every table, and access is not granted to `anon` or `authenticated`. API access is server-side only using a private Postgres connection string.

## Publish the curated panel
Set GitHub Actions secret `SUPABASE_DB_URL` to the Supabase Postgres connection string. Prefer the transaction pooler connection string for hosted services and require TLS. Do not use the service-role API key as a database password.

Run after `scripts.prepare_data`:
```bash
python -m scripts.load_retail_warehouse
```
The loader validates required columns, stages data with COPY, upserts dimensions, and publishes an immutable dataset run. Re-running the same Parquet artifact replaces only the matching version. It never downloads or stores a second copy of the source ZIP.

## API configuration
Set Render environment variable `SUPABASE_DB_URL` to the same private database connection string. The analytics API opens read-only transactions. If it is absent, existing forecast and inventory routes continue to work; analytics routes return HTTP 503 with a configuration message.

## Analytical limitations
- M5 has sales, prices, calendar events and SNAP indicators; it does not contain on-hand inventory, supplier lead times, holding costs, order costs or lost-sales costs.
- Inventory recommendations are scenario outputs using user-supplied assumptions, not observed stock positions or verified savings.
- Price-demand relationships are observational and should not be described as causal.
- Weekday significance is exploratory and uses within-week label permutation; block bootstrap intervals retain short-range time dependence.
