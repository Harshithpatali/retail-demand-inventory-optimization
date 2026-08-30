import joblib
import pandas as pd
from src.utils.config import ROOT
from src.forecasting.predict import recursive_global_forecast
from src.uncertainty.prediction_intervals import normal_interval

def main():
    artifact=ROOT/"models/forecasting/best_model.joblib"; data=ROOT/"data/processed/forecast_features.parquet"; stats_path=ROOT/"models/uncertainty/residual_stats.joblib"
    if not artifact.exists() or not data.exists() or not stats_path.exists(): raise FileNotFoundError("Missing forecasting artifacts. Run the complete training pipeline first.")
    bundle=joblib.load(artifact); stats=joblib.load(stats_path); df=pd.read_parquet(data)
    rows=[]
    for sid,g in df.groupby("id",observed=True):
        hist=g.sort_values("date").tail(56); future=pd.date_range(df.date.max()+pd.Timedelta(days=1), periods=28, freq="D")
        b=dict(bundle); b.update({"store_code":int(g.store_code.iloc[-1]),"item_code":int(g.item_code.iloc[-1]),"dept_code":int(g.dept_code.iloc[-1]),"cat_code":int(g.cat_code.iloc[-1]),"state_code":int(g.state_code.iloc[-1])})
        pred=recursive_global_forecast(b,hist,future); lo,hi=normal_interval(pred.forecast,stats["std"]); pred["lower"]=lo; pred["upper"]=hi; pred["id"]=sid; rows.append(pred)
    out=pd.concat(rows,ignore_index=True); out.to_parquet(ROOT/"data/processed/forecast_output.parquet",index=False); print(f"Generated {len(out):,} forecast rows.")
if __name__=="__main__":
    try: main()
    except (FileNotFoundError,ValueError,RuntimeError,KeyError) as exc: print(f"ERROR: {exc}"); raise SystemExit(1)
