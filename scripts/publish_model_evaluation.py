"""Publish empirical evaluation tables into the private Supabase retail schema."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
REQUIRED = [
    "rolling_origin_refit_by_fold.csv",
    "forecast_metrics_by_demand_segment.csv",
    "conformal_interval_diagnostics.csv",
    "inventory_sensitivity_summary.csv",
]


def main() -> None:
    dsn = os.getenv("SUPABASE_DB_URL", "").strip()
    if not dsn:
        raise RuntimeError("SUPABASE_DB_URL is required to publish evaluation results.")
    paths = [TABLES / name for name in REQUIRED]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing evaluation outputs: {missing}")

    frames = {path.name: pd.read_csv(path) for path in paths}
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    evaluation_run = os.getenv("GITHUB_SHA") or digest.hexdigest()

    fold = frames["rolling_origin_refit_by_fold.csv"]
    segment = frames["forecast_metrics_by_demand_segment.csv"]
    intervals = frames["conformal_interval_diagnostics.csv"]
    sensitivity = frames["inventory_sensitivity_summary.csv"]

    model_rows = []
    for row in fold.to_dict("records"):
        model_rows.append((
            evaluation_run, str(row["model"]), "all", int(row["fold"]),
            int(row["test_rows"]), float(row["MAE"]), float(row["RMSE"]),
            float(row["WAPE"]), (None if pd.isna(row.get("bias")) else float(row["bias"])), "{}"
        ))
    for row in segment.to_dict("records"):
        model_rows.append((
            evaluation_run, str(row["model"]), str(row["demand_segment"]), None,
            int(row["sample_count"]), float(row["MAE"]), float(row["RMSE"]),
            float(row["WAPE"]), None, "{}"
        ))

    with psycopg.connect(dsn, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("delete from retail.model_evaluation where evaluation_run=%s", (evaluation_run,))
            cur.execute("delete from retail.forecast_interval_evaluation where evaluation_run=%s", (evaluation_run,))
            cur.execute("delete from retail.inventory_sensitivity where evaluation_run=%s", (evaluation_run,))
            cur.executemany("""
                insert into retail.model_evaluation
                (evaluation_run,model_name,demand_segment,fold,sample_count,mae,rmse,wape,bias,metadata)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            """, model_rows)

            interval_rows = [
                (evaluation_run, float(r["nominal_coverage"]), float(r["empirical_coverage"]),
                 float(r["mean_interval_width"]), int(r["observations"]), str(r["calibration"]), "{}")
                for r in intervals.to_dict("records")
            ]
            cur.executemany("""
                insert into retail.forecast_interval_evaluation
                (evaluation_run,nominal_coverage,empirical_coverage,mean_interval_width,observations,calibration_method,metadata)
                values (%s,%s,%s,%s,%s,%s,%s::jsonb)
            """, interval_rows)

            sensitivity_rows = []
            for r in sensitivity.to_dict("records"):
                sensitivity_rows.append((
                    evaluation_run, int(r["lead_time_days"]), int(r["review_period_days"]),
                    float(r["service_level_target"]), str(r["cost_scenario"]), int(r["series_count"]),
                    float(r["baseline_total_cost"]), float(r["candidate_total_cost"]),
                    float(r["baseline_stockout_units"]), float(r["candidate_stockout_units"]),
                    float(r["baseline_fill_rate"]), float(r["candidate_fill_rate"]),
                    float(r["baseline_average_inventory"]), float(r["candidate_average_inventory"]),
                    None if pd.isna(r.get("cost_change_pct_vs_80pct")) else float(r["cost_change_pct_vs_80pct"]),
                    None if pd.isna(r.get("stockout_change_pct_vs_80pct")) else float(r["stockout_change_pct_vs_80pct"]),
                ))
            cur.executemany("""
                insert into retail.inventory_sensitivity
                (evaluation_run,lead_time_days,review_period_days,service_level_target,cost_scenario,
                 series_count,baseline_total_cost,candidate_total_cost,baseline_stockout_units,
                 candidate_stockout_units,baseline_fill_rate,candidate_fill_rate,
                 baseline_average_inventory,candidate_average_inventory,cost_change_pct,stockout_change_pct)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, sensitivity_rows)
        conn.commit()
    print(f"Published {len(model_rows)} model metric rows, {len(interval_rows)} interval rows, "
          f"and {len(sensitivity_rows)} inventory sensitivity rows for {evaluation_run}.")


if __name__ == "__main__":
    main()
