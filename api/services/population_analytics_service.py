"""Read compact full-population M5 EDA artifacts from private Cloudflare R2."""
from __future__ import annotations
import json, os
from functools import lru_cache
from io import BytesIO
from typing import Any
import boto3
import pandas as pd
from botocore.config import Config

def _client():
    account=os.getenv("R2_ACCOUNT_ID","").strip()
    access=os.getenv("R2_ACCESS_KEY_ID","").strip()
    secret=os.getenv("R2_SECRET_ACCESS_KEY","").strip()
    if not all((account,access,secret)):
        raise RuntimeError("Cloudflare R2 is not configured. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY on the API service.")
    return boto3.client("s3",endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
        aws_access_key_id=access,aws_secret_access_key=secret,region_name="auto",
        config=Config(signature_version="s3v4",connect_timeout=5,read_timeout=25,
                      retries={"max_attempts":3,"mode":"standard"}))
def _bucket(): return os.getenv("R2_BUCKET","m5-retail-analytics").strip()
@lru_cache(maxsize=8)
def _json(key):
    obj=_client().get_object(Bucket=_bucket(),Key=key)
    return json.loads(obj["Body"].read())
@lru_cache(maxsize=8)
def _csv(key):
    obj=_client().get_object(Bucket=_bucket(),Key=key)
    return pd.read_csv(BytesIO(obj["Body"].read()))
def _records(frame):
    clean = frame.astype(object).where(pd.notna(frame), None)
    clean = clean.replace([float("inf"), float("-inf")], None)
    return clean.to_dict(orient="records")
class PopulationAnalyticsService:
    prefix="processed/full_population_eda/"
    def status(self):
        manifest=_json("metadata/manifest.json")
        keys={x.get("key") for x in manifest.get("objects",[])}
        required={self.prefix+"full_eda_summary.json",self.prefix+"series_metrics.csv",self.prefix+"daily_demand_full_population.csv"}
        missing=sorted(required-keys)
        return {"available":not missing,"bucket":_bucket(),"manifest_created_at":manifest.get("created_at_utc"),
                "object_count":len(manifest.get("objects",[])),"missing_eda_objects":missing,
                "scope":"full_population_eda"}
    def overview(self):
        x=_json(self.prefix+"full_eda_summary.json")
        return {"available":True,"scope":"full_population","source":x.get("source_sales_file"),
            "series_count":int(x.get("series_count",0)),"date_count":int(x.get("date_count",0)),
            "first_date":x.get("first_date"),"last_date":x.get("last_date"),
            "total_units":float(x.get("total_units",0)),"active_series":int(x.get("active_series",0)),
            "inactive_series":int(x.get("inactive_series",0)),
            "median_zero_day_fraction":float(x.get("series_zero_fraction_median",0)),
            "mean_zero_day_fraction":float(x.get("series_zero_fraction_mean",0)),
            "median_series_total_demand":float(x.get("series_total_demand_median",0)),
            "price_records":int(x.get("price_records",0)),"price_missing_values":int(x.get("price_missing_values",0)),
            "storage":"Cloudflare R2"}
    def segments(self,dimension):
        if dimension not in {"state_id","store_id","cat_id","dept_id"}:
            raise ValueError("dimension must be state_id, store_id, cat_id or dept_id")
        return _records(_csv(self.prefix+f"by_{dimension}.csv"))
    def series(self,limit=100,offset=0,store_id=None,state_id=None,cat_id=None,dept_id=None,sort_by="total_units"):
        allowed={"total_units","mean_daily_demand","zero_day_fraction","average_demand_interval","demand_cv_squared"}
        if sort_by not in allowed: raise ValueError(f"sort_by must be one of {sorted(allowed)}")
        frame=_csv(self.prefix+"series_metrics.csv")
        for col,val in (("store_id",store_id),("state_id",state_id),("cat_id",cat_id),("dept_id",dept_id)):
            if val: frame=frame[frame[col].astype(str)==str(val)]
        frame=frame.sort_values(sort_by,ascending=False,na_position="last")
        total=len(frame); offset=max(0,offset); limit=max(1,min(limit,500))
        return {"total":int(total),"limit":limit,"offset":offset,"rows":_records(frame.iloc[offset:offset+limit])}
    def daily(self):
        frame=_csv(self.prefix+"daily_demand_full_population.csv")
        cols=[c for c in ("date","total_units","active_series","series_count","weekday_name","month_label",
                          "event_name_1","event_type_1","snap_CA","snap_TX","snap_WI") if c in frame.columns]
        return _records(frame[cols])

    def forecast_status(self):
        key="processed/full_population_forecasting/forecast_run_metadata.json"
        try:
            meta=_json(key)
        except Exception:
            return {"available":False,"reason":"Full-population forecast metadata is not published to R2 yet."}
        return {"available":True,"scope":"full_population_forecast","series_count":meta.get("population_series"),
            "forecast_rows":meta.get("forecast_rows"),"forecast_unique_series":meta.get("forecast_unique_series"),
            "horizon_days":meta.get("horizon_days"),"forecast_start":meta.get("forecast_start"),
            "forecast_end":meta.get("forecast_end"),"selected_training_sample_pct":meta.get("selected_training_sample_pct"),
            "peak_process_rss_gb":meta.get("peak_process_rss_gb"),"inventory_assumptions":meta.get("inventory_assumptions"),
            "limitations":meta.get("limitations")}
    def forecast_metrics(self):
        key="processed/full_population_forecasting/full_population_forecast_metrics.csv"
        try:
            return _records(_csv(key))
        except Exception:
            raise RuntimeError("Full-population forecast metrics are not published to R2 yet.")
    def forecast_sample_comparison(self):
        key="processed/full_population_forecasting/training_sample_comparison.csv"
        try:
            return _records(_csv(key))
        except Exception:
            raise RuntimeError("Training-sample comparison is not published to R2 yet.")
