import numpy as np
import pandas as pd

def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))

def rmse(y_true, y_pred) -> float:
    err = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.sqrt(np.mean(err ** 2)))

def wape(y_true, y_pred) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    denom = np.sum(np.abs(y))
    return float(np.sum(np.abs(y-p)) / denom) if denom else 0.0

def evaluate(y_true, y_pred) -> dict:
    return {"MAE": mae(y_true, y_pred), "RMSE": rmse(y_true, y_pred), "WAPE": wape(y_true, y_pred)}

def error_by_demand_segment(df: pd.DataFrame, actual_col="demand", pred_col="prediction") -> pd.DataFrame:
    q = df.groupby("id", observed=True)[actual_col].sum().rename("series_volume")
    x = df.join(q, on="id")
    x["demand_segment"] = pd.qcut(x["series_volume"], q=[0,0.5,0.8,1.0], labels=["low","medium","high"], duplicates="drop")
    rows=[]
    for seg, g in x.groupby("demand_segment", observed=True):
        m=evaluate(g[actual_col], g[pred_col]); m["demand_segment"]=str(seg); rows.append(m)
    return pd.DataFrame(rows)
