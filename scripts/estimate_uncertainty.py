import joblib
import pandas as pd
from src.utils.config import ROOT, load_yaml
from src.forecasting.evaluate import evaluate
from src.uncertainty.demand_distribution import residual_statistics

def main():
    model_cfg=load_yaml("model_config.yaml")
    features=ROOT/"data/processed/forecast_features.parquet"; artifact=ROOT/"models/forecasting/validation_model.joblib"
    if not features.exists() or not artifact.exists(): raise FileNotFoundError("Missing forecasting artifacts. Run python -m scripts.train_models first.")
    df=pd.read_parquet(features); maxd=df.date.max(); test_start=maxd-pd.Timedelta(days=model_cfg["test_days"]-1); val_start=test_start-pd.Timedelta(days=model_cfg["validation_days"]); val=df[(df.date>=val_start)&(df.date<test_start)]
    bundle=joblib.load(artifact); pred=bundle["model"].predict(val[bundle["feature_columns"]]).clip(min=0); residual=val["demand"].to_numpy()-pred
    stats=residual_statistics(residual); stats.update(evaluate(val["demand"],pred)); stats.update({"period_start":str(val.date.min().date()),"period_end":str(val.date.max().date()),"source":"out_of_sample_validation"})
    joblib.dump(stats,ROOT/"models/uncertainty/residual_stats.joblib"); print(stats)
if __name__=="__main__":
    try: main()
    except (FileNotFoundError,ValueError,RuntimeError,KeyError) as exc: print(f"ERROR: {exc}"); raise SystemExit(1)
