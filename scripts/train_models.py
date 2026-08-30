import joblib
import pandas as pd
import matplotlib.pyplot as plt
from src.utils.config import ROOT, load_yaml
from src.features.feature_pipeline import MODEL_FEATURES
from src.forecasting.train import train_candidates
from src.forecasting.evaluate import evaluate
from src.forecasting.baselines import naive_forecast, seasonal_naive_forecast, moving_average_forecast

def split(df, val_days, test_days):
    maxd=df["date"].max(); test_start=maxd-pd.Timedelta(days=test_days-1); val_start=test_start-pd.Timedelta(days=val_days)
    return df[df.date<val_start], df[(df.date>=val_start)&(df.date<test_start)], df[df.date>=test_start]

def main():
    model_cfg=load_yaml("model_config.yaml"); src=ROOT/"data/processed/forecast_features.parquet"
    if not src.exists(): raise FileNotFoundError("Missing prerequisite: forecast_features.parquet. Run python -m scripts.build_features first.")
    df=pd.read_parquet(src); train,val,test=split(df,model_cfg["validation_days"],model_cfg["test_days"])
    candidates=train_candidates(train,val,MODEL_FEATURES,model_cfg)
    rows=[{"model":c.name,**c.metrics} for c in candidates]
    bpred={"naive":[],"seasonal_naive":[],"moving_average":[]}; y=[]
    for sid,g in val.groupby("id",observed=True):
        hist=train[train.id==sid].sort_values("date")["demand"]; yt=g.sort_values("date")["demand"].to_numpy(); y.extend(yt)
        bpred["naive"].extend(naive_forecast(hist,len(yt))); bpred["seasonal_naive"].extend(seasonal_naive_forecast(hist,len(yt))); bpred["moving_average"].extend(moving_average_forecast(hist,len(yt)))
    for name,p in bpred.items(): rows.append({"model":name,**evaluate(y,p)})
    result=pd.DataFrame(rows).sort_values("WAPE"); result.to_csv(ROOT/"reports/tables/model_comparison_validation.csv",index=False)
    fig_dir=ROOT/"reports/figures/forecasting"; fig_dir.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(8,4)); result.sort_values("WAPE").plot(x="model",y="WAPE",kind="bar",ax=ax,legend=False); ax.set_title("Validation WAPE by Model"); ax.set_ylabel("WAPE"); fig.tight_layout(); fig.savefig(fig_dir/"model_comparison.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    ml_best=result[result.model.isin(["xgboost","lightgbm"])].iloc[0]["model"]; selected=next(c for c in candidates if c.name==ml_best)
    refit=pd.concat([train,val],ignore_index=True)
    if ml_best=="xgboost":
        from src.forecasting.xgboost_model import build_xgboost; final_model=build_xgboost(model_cfg["xgboost"],model_cfg["random_seed"],model_cfg["n_jobs"])
    else:
        from src.forecasting.lightgbm_model import build_lightgbm; final_model=build_lightgbm(model_cfg["lightgbm"],model_cfg["random_seed"],model_cfg["n_jobs"])
    final_model.fit(refit[MODEL_FEATURES],refit["demand"])
    bundle={"model_name":ml_best,"model":final_model,"feature_columns":MODEL_FEATURES,"train_end":str(refit.date.max())}
    joblib.dump(bundle,ROOT/f"models/forecasting/{ml_best}.joblib"); joblib.dump(bundle,ROOT/"models/forecasting/best_model.joblib")
    joblib.dump({"model_name":selected.name,"model":selected.model,"feature_columns":MODEL_FEATURES},ROOT/"models/forecasting/validation_model.joblib")
    imp=pd.Series(final_model.feature_importances_,index=MODEL_FEATURES).sort_values(ascending=False).head(15)
    fig,ax=plt.subplots(figsize=(8,5)); imp.sort_values().plot(kind="barh",ax=ax); ax.set_title(f"{ml_best.upper()} Feature Importance"); fig.tight_layout(); fig.savefig(fig_dir/"feature_importance.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    pred_val=selected.model.predict(val[MODEL_FEATURES]).clip(min=0); sample_sid=sorted(val.id.astype(str).unique())[0]; actual=val[val.id.astype(str)==sample_sid].sort_values("date"); sample_pred=selected.model.predict(actual[MODEL_FEATURES]).clip(min=0)
    fig,ax=plt.subplots(figsize=(10,4)); ax.plot(actual.date,actual.demand,label="Actual"); ax.plot(actual.date,sample_pred,label="Forecast"); ax.legend(); ax.set_title(f"Validation Forecast vs Actual — {sample_sid}"); fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(fig_dir/"forecast_vs_actual.png",dpi=160,bbox_inches="tight"); plt.close(fig)
    print(result.to_string(index=False)); print(f"Selected ML model: {ml_best}")
if __name__=="__main__":
    try: main()
    except (FileNotFoundError,ValueError,RuntimeError,KeyError) as exc: print(f"ERROR: {exc}"); raise SystemExit(1)
