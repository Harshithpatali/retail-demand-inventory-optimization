import pandas as pd

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["day_of_week"] = x["date"].dt.dayofweek.astype("int8")
    x["week_of_year"] = x["date"].dt.isocalendar().week.astype("int16")
    x["month"] = x["date"].dt.month.astype("int8")
    x["quarter"] = x["date"].dt.quarter.astype("int8")
    x["day_of_month"] = x["date"].dt.day.astype("int8")
    x["is_weekend"] = x["day_of_week"].isin([5, 6]).astype("int8")
    x["event_flag"] = (~x["event_name_1"].isna() | ~x["event_name_2"].isna()).astype("int8") if "event_name_1" in x.columns else 0
    x["snap_flag"] = 0
    for c in ["snap_CA", "snap_TX", "snap_WI"]:
        if c in x.columns:
            x.loc[x["state_id"].astype(str).eq(c.split("_")[-1]), "snap_flag"] = x.loc[x["state_id"].astype(str).eq(c.split("_")[-1]), c].fillna(0).astype("int8")
    return x
