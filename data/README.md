# M5 source data and generated datasets

## Private raw source

The original M5 competition archive is stored in the private Supabase Storage bucket
`m5-raw-data`. Raw CSV files are intentionally excluded from Git history to avoid
large source-data commits and to keep the original archive private.

The manual GitHub Actions workflow
[`process-m5-source-data`](../.github/workflows/process-m5-source-data.yml):

1. Authenticates to Supabase Storage using repository Actions secrets.
2. Finds the single ZIP in `m5-raw-data`, or uses the optional `M5_ZIP_PATH` secret.
3. Verifies ZIP integrity and extracts the five source CSV files into the runner's
   ignored `data/raw/` directory.
4. Runs `scripts.prepare_data` and `scripts.build_features`.
5. Validates the generated outputs and commits only the processed data to `main`.

Required GitHub repository secrets:

- `SUPABASE_URL`: project URL.
- `SUPABASE_SECRET_KEY`: server-side Supabase secret key. The workflow also accepts
  the legacy `SUPABASE_SERVICE_ROLE_KEY` name.

Optional secret:

- `M5_ZIP_PATH`: exact ZIP object path inside the bucket, useful if multiple ZIPs
  are stored there.

Never put Supabase credentials in source files, Streamlit code, or committed
configuration. The bucket should remain private.

## Source CSV files

The complete archive must contain these five files:

- `sales_train_evaluation.csv`
- `sales_train_validation.csv`
- `calendar.csv`
- `sell_prices.csv`
- `sample_submission.csv`

## Generated data committed to this repository

- `data/interim/cleaned_sales.parquet`: cleaned long-form demand panel for the
  deterministic selected item-store series.
- `data/interim/validation_report.json`: compact source-data and cleaning checks.
- `data/processed/forecast_features.parquet`: model-ready panel with lag,
  rolling, calendar and price features.

Raw source files in `data/raw/` are ignored by Git and are never committed by
the processing workflow. The default experiment selects up to 20 items per store
and 200 total item-store series; see `configs/data_config.yaml`.
