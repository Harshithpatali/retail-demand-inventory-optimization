import numpy as np
import pandas as pd
from src.forecasting.baselines import naive_forecast, seasonal_naive_forecast, moving_average_forecast

def recursive_global_forecast(model_bundle: dict, history_df: pd.DataFrame, future_dates: pd.DatetimeIndex, calendar_df: pd.DataFrame | None = None) -> pd.DataFrame:
    model = model_bundle["model"]
    feature_columns = model_bundle["feature_columns"]
    row = history_df.sort_values("date").copy()
    if row.empty:
        raise ValueError("History is empty.")
    predictions=[]
    prices = row["sell_price"].dropna()
    last_price = float(prices.iloc[-1]) if len(prices) else 0.0
    values = list(row["demand"].astype(float).to_numpy())
    for date in future_dates:
        f = {
            "day_of_week": date.dayofweek,
            "week_of_year": int(date.isocalendar().week),
            "month": date.month,
            "quarter": (date.month-1)//3+1,
            "day_of_month": date.day,
            "is_weekend": int(date.dayofweek>=5),
            "event_flag": 0,
            "snap_flag": 0,
            "sell_price": last_price,
            "price_change_pct": 0.0,
            "store_code": int(model_bundle.get("store_code",0)),
            "item_code": int(model_bundle.get("item_code",0)),
            "dept_code": int(model_bundle.get("dept_code",0)),
            "cat_code": int(model_bundle.get("cat_code",0)),
            "state_code": int(model_bundle.get("state_code",0)),
        }
        for lag in [1,7,14,28]:
            f[f"lag_{lag}"] = values[-lag] if len(values)>=lag else 0.0
        for w in [7,14,28]:
            vals = np.asarray(values[-w:], dtype=float) if values else np.array([0.0])
            f[f"rolling_mean_{w}"] = float(vals.mean())
            f[f"rolling_std_{w}"] = float(vals.std(ddof=1)) if len(vals)>1 else 0.0
        X = pd.DataFrame([f])[feature_columns]
        pred = float(np.clip(model.predict(X)[0], 0, None))
        predictions.append(pred)
        values.append(pred)
    return pd.DataFrame({"date": future_dates, "forecast": predictions})
