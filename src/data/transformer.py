import pandas as pd


def series_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("id", observed=True)["demand"]
    out = g.agg(["sum", "mean", "std", "max"]).rename(columns={"sum":"total_demand"})
    out["zero_rate"] = g.apply(lambda s: float((s == 0).mean()))
    return out.reset_index()
