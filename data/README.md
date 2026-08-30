# Raw M5 data placement

Place these five files directly in `data/raw/`:

- `sales_train_evaluation.csv`
- `sales_train_validation.csv`
- `calendar.csv`
- `sell_prices.csv`
- `sample_submission.csv`

The project prefers `sales_train_evaluation.csv` and falls back to `sales_train_validation.csv`. Raw files are intentionally not included in the ZIP.

The local pipeline selects a deterministic demand-ranked subset. Default: up to 20 items per store and 200 total item-store series. This is intentionally a portfolio-scale experiment for a 15 GB RAM CPU-only machine.
