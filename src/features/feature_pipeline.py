from pathlib import Path
import pandas as pd
from src.features.time_features import add_time_features
from src.features.lag_features import add_lag_features
from src.features.rolling_features import add_rolling_features
from src.features.price_features import add_price_features

MODEL_FEATURES = [
    "store_code", "item_code", "dept_code", "cat_code", "state_code",
    "day_of_week", "week_of_year", "month", "quarter", "day_of_month", "is_weekend",
    "event_flag", "snap_flag", "sell_price", "price_change_pct",
    "lag_1", "lag_7", "lag_14", "lag_28",
    "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_std_14",
    "rolling_mean_28", "rolling_std_28",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    x = add_time_features(df)
    x = add_lag_features(x)
    x = add_rolling_features(x)
    x = add_price_features(x)
    for col, src in [("store_code","store_id"),("item_code","item_id"),("dept_code","dept_id"),("cat_code","cat_id"),("state_code","state_id")]:
        x[col] = x[src].astype("category").cat.codes.astype("int16")
    for c in MODEL_FEATURES:
        if c not in x.columns:
            x[c] = 0
    x[MODEL_FEATURES] = x[MODEL_FEATURES].replace([float("inf"), float("-inf")], pd.NA).fillna(0)
    return x
