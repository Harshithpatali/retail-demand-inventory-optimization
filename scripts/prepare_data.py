import json
import pandas as pd
import matplotlib.pyplot as plt
from src.utils.config import ROOT, load_yaml
from src.data.loader import raw_paths, select_sales_file, choose_top_series, load_selected_sales_long, load_calendar, load_prices
from src.data.cleaner import clean_sales_panel
from src.data.validator import validate_raw_files, build_validation_report

def main():
    cfg=load_yaml("data_config.yaml")
    paths=raw_paths(ROOT)
    missing=validate_raw_files(ROOT/"data/raw")
    if missing:
        raise FileNotFoundError("Missing required file(s) in data/raw/:\n" + "\n".join(missing))
    sales_path=select_sales_file(paths,cfg["preferred_sales_file"],cfg["fallback_sales_file"])
    selected=choose_top_series(sales_path,cfg["max_items_per_store"],cfg["max_total_series"],cfg["selection_days"],cfg["chunk_rows"])
    sales_long=load_selected_sales_long(sales_path,set(selected),cfg["chunk_rows"])
    calendar=load_calendar(paths["calendar"]); prices=load_prices(paths["prices"])
    cleaned=clean_sales_panel(sales_long,calendar,prices)
    out=ROOT/"data/interim/cleaned_sales.parquet"; cleaned.to_parquet(out,index=False)
    report=build_validation_report(ROOT/"data/raw",cleaned,calendar,prices); report["series_selection_rule"]=f"Top {cfg['max_items_per_store']} items per store by last {cfg['selection_days']} days demand, capped at {cfg['max_total_series']} total series."; report["sales_source"]=sales_path.name
    (ROOT/"data/interim/validation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    fig_dir=ROOT/"reports/figures/eda"; fig_dir.mkdir(parents=True,exist_ok=True)
    daily=cleaned.groupby("date",observed=True)["demand"].sum()
    fig,ax=plt.subplots(figsize=(10,4)); daily.plot(ax=ax); ax.set_title("Total Daily Demand"); ax.set_ylabel("Units"); fig.tight_layout(); fig.savefig(fig_dir/"daily_sales.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    print(f"Prepared {cleaned['id'].nunique()} series and {len(cleaned):,} rows.")
if __name__=="__main__":
    try: main()
    except (FileNotFoundError,ValueError,RuntimeError,KeyError) as exc: print(f"ERROR: {exc}"); raise SystemExit(1)
