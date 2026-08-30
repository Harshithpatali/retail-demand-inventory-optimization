import pandas as pd

def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    if "sell_price" not in x.columns:
        x["sell_price"] = 0.0
    x["price_change_pct"] = (
        x.groupby("id", sort=False, observed=True)["sell_price"]
        .pct_change(fill_method=None)
        .replace([float("inf"), float("-inf")], pd.NA)
        .fillna(0)
        .astype("float32")
    )
    return x
