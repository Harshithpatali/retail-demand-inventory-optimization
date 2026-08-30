import pandas as pd

def add_lag_features(df: pd.DataFrame, lags=(1,7,14,28)) -> pd.DataFrame:
    x = df.copy()
    grp = x.groupby("id", observed=True)["demand"]
    for lag in lags:
        x[f"lag_{lag}"] = grp.shift(lag)
    return x
