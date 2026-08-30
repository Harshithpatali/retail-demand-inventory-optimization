import pandas as pd

def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    grp = x.groupby("id", observed=True)["demand"]
    for w in (7,14,28):
        x[f"rolling_mean_{w}"] = grp.transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
        x[f"rolling_std_{w}"] = grp.transform(lambda s: s.shift(1).rolling(w, min_periods=2).std())
    return x
