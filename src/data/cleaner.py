import pandas as pd


def clean_sales_panel(sales_long: pd.DataFrame, calendar: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    x = sales_long.merge(calendar, on="d", how="left", validate="many_to_one")
    price_cols = ["store_id", "item_id", "wm_yr_wk", "sell_price"]
    x = x.merge(prices[price_cols], on=["store_id", "item_id", "wm_yr_wk"], how="left", validate="many_to_one")
    x["sell_price"] = x.groupby("id", observed=True)["sell_price"].ffill().bfill()
    x["sell_price"] = x["sell_price"].astype("float32")
    x["date"] = pd.to_datetime(x["date"])
    x["weekday"] = x["weekday"].astype("category")
    for c in ["store_id", "item_id", "dept_id", "cat_id", "state_id"]:
        x[c] = x[c].astype("category")
    x["demand"] = x["demand"].astype("int16")
    return x.sort_values(["id", "date"]).reset_index(drop=True)
