"""Publish the compact selected M5 panel to the private Supabase retail mart.

The raw ZIP remains in Supabase Storage. This script only uploads the curated
item-store-day panel produced by scripts.prepare_data.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "interim" / "cleaned_sales.parquet"
CHUNK_SIZE = 40_000
COLUMNS = [
    "store_id", "item_id", "dept_id", "cat_id", "state_id", "calendar_date",
    "d", "weekday", "wday", "month", "year", "wm_yr_wk", "demand",
    "sell_price", "event_name_1", "event_type_1", "event_name_2",
    "event_type_2", "snap_ca", "snap_tx", "snap_wi",
]
OPTIONAL_DEFAULTS = {
    "event_name_1": None, "event_type_1": None, "event_name_2": None,
    "event_type_2": None, "snap_CA": False, "snap_TX": False, "snap_WI": False,
    "sell_price": None,
}

def _version(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    required = {"store_id", "item_id", "dept_id", "cat_id", "state_id", "date", "d", "demand"}
    missing = required - set(x.columns)
    if missing:
        raise ValueError(f"Cleaned panel is missing required columns: {sorted(missing)}")
    for column, default in OPTIONAL_DEFAULTS.items():
        if column not in x:
            x[column] = default
    x["calendar_date"] = pd.to_datetime(x["date"], errors="raise").dt.strftime("%Y-%m-%d")
    x["demand"] = pd.to_numeric(x["demand"], errors="raise").astype("int64")
    if (x["demand"] < 0).any():
        raise ValueError("Demand must be non-negative.")
    x["sell_price"] = pd.to_numeric(x["sell_price"], errors="coerce")
    x = x.rename(columns={"snap_CA": "snap_ca", "snap_TX": "snap_tx", "snap_WI": "snap_wi"})
    for column in ("snap_ca", "snap_tx", "snap_wi"):
        x[column] = x[column].fillna(False).astype(bool)
    x["wday"] = pd.to_numeric(x.get("wday"), errors="coerce").astype("Int64")
    x["month"] = pd.to_numeric(x.get("month"), errors="coerce").astype("Int64")
    x["year"] = pd.to_numeric(x.get("year"), errors="coerce").astype("Int64")
    x["wm_yr_wk"] = pd.to_numeric(x.get("wm_yr_wk"), errors="coerce").astype("Int64")
    for column in COLUMNS:
        if column not in x:
            x[column] = None
    return x[COLUMNS]

def main() -> None:
    dsn = os.getenv("SUPABASE_DB_URL", "").strip()
    if not dsn:
        raise RuntimeError("SUPABASE_DB_URL is missing. Add the Supabase Postgres connection string as a GitHub Actions secret.")
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing curated panel: {SOURCE}. Run scripts.prepare_data first.")

    frame = pd.read_parquet(SOURCE)
    frame = _prepare(frame)
    if frame.empty:
        raise ValueError("Refusing to publish an empty retail panel.")
    dataset_version = _version(SOURCE)
    source_bucket = os.getenv("SUPABASE_BUCKET", "m5-raw-data")
    source_object = os.getenv("M5_ZIP_PATH", "").strip() or "m5-forecasting-accuracy.zip"
    start_date = frame["calendar_date"].min()
    end_date = frame["calendar_date"].max()
    row_count = len(frame)
    series_count = frame[["store_id", "item_id"]].drop_duplicates().shape[0]

    create_stage = """
    create temp table _m5_stage (
      store_id text, item_id text, dept_id text, cat_id text, state_id text,
      calendar_date date, d text, weekday text, wday smallint, month smallint,
      year smallint, wm_yr_wk integer, demand integer, sell_price numeric(12,4),
      event_name_1 text, event_type_1 text, event_name_2 text, event_type_2 text,
      snap_ca boolean, snap_tx boolean, snap_wi boolean
    ) on commit drop
    """
    with psycopg.connect(dsn, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(create_stage)
            copy_sql = (
                "COPY _m5_stage (" + ",".join(COLUMNS) +
                ") FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
            )
            with cur.copy(copy_sql) as copy:
                for start in range(0, row_count, CHUNK_SIZE):
                    buffer = io.StringIO()
                    frame.iloc[start:start + CHUNK_SIZE].to_csv(
                        buffer, index=False, header=False, na_rep=r"\N",
                        date_format="%Y-%m-%d"
                    )
                    copy.write(buffer.getvalue())

            cur.execute(
                "delete from retail.dataset_runs where dataset_version=%s and source_bucket=%s and source_object=%s",
                (dataset_version, source_bucket, source_object),
            )
            cur.execute(
                """insert into retail.dataset_runs
                   (source_bucket,source_object,dataset_version,row_count,series_count,start_date,end_date,metadata)
                   values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb) returning run_id""",
                (source_bucket,source_object,dataset_version,row_count,series_count,start_date,end_date,
                 '{"panel":"selected_high_demand_series","raw_archive_retained_in_storage":true}'),
            )
            run_id = cur.fetchone()[0]

            cur.execute("""insert into retail.dim_product(item_id,dept_id,cat_id)
                select distinct item_id,dept_id,cat_id from _m5_stage
                on conflict(item_id) do update set dept_id=excluded.dept_id,cat_id=excluded.cat_id""")
            cur.execute("""insert into retail.dim_store(store_id,state_id)
                select distinct store_id,state_id from _m5_stage
                on conflict(store_id) do update set state_id=excluded.state_id""")
            cur.execute("""insert into retail.dim_date
                (calendar_date,d,weekday,wday,month,year,wm_yr_wk,event_name_1,event_type_1,event_name_2,event_type_2,snap_ca,snap_tx,snap_wi)
                select distinct on(calendar_date) calendar_date,d,weekday,wday,month,year,wm_yr_wk,
                       event_name_1,event_type_1,event_name_2,event_type_2,snap_ca,snap_tx,snap_wi
                from _m5_stage order by calendar_date
                on conflict(calendar_date) do update set d=excluded.d,weekday=excluded.weekday,
                  wday=excluded.wday,month=excluded.month,year=excluded.year,wm_yr_wk=excluded.wm_yr_wk,
                  event_name_1=excluded.event_name_1,event_type_1=excluded.event_type_1,
                  event_name_2=excluded.event_name_2,event_type_2=excluded.event_type_2,
                  snap_ca=excluded.snap_ca,snap_tx=excluded.snap_tx,snap_wi=excluded.snap_wi""")
            cur.execute("""insert into retail.fact_daily_demand
                (run_id,store_id,item_id,calendar_date,demand,sell_price)
                select %s,store_id,item_id,calendar_date,demand,sell_price from _m5_stage
                on conflict(run_id,store_id,item_id,calendar_date) do update
                set demand=excluded.demand,sell_price=excluded.sell_price""", (run_id,))
        conn.commit()
    print(f"Published {row_count:,} daily rows across {series_count:,} item-store series.")
    print(f"Dataset version: {dataset_version}; date range: {start_date} to {end_date}; run_id={run_id}")

if __name__ == "__main__":
    main()
