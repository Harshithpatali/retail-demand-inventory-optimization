import pandas as pd

def summarize_simulation(df: pd.DataFrame) -> dict:
    demand=float(df["demand"].sum()); fulfilled=float(df["fulfilled"].sum())
    return {
        "total_cost": float(df["total_cost"].sum()),
        "holding_cost": float(df["holding_cost"].sum()),
        "ordering_cost": float(df["ordering_cost"].sum()),
        "stockout_cost": float(df["stockout_cost"].sum()),
        "average_inventory": float(df["ending_inventory"].mean()),
        "max_inventory": float(df["ending_inventory"].max()),
        "stockout_units": float(df["stockout_units"].sum()),
        "stockout_days": int((df["stockout_units"]>0).sum()),
        "service_level": float(fulfilled/demand) if demand else 1.0,
        "fill_rate": float(fulfilled/demand) if demand else 1.0,
        "orders": int((df["order_quantity_placed"]>0).sum()),
    }

def compare(baseline: dict, optimized: dict) -> list[dict]:
    rows=[]
    for metric in baseline:
        b=float(baseline[metric]); o=float(optimized[metric])
        pct=(o-b)/b*100 if b!=0 else float("nan")
        rows.append({"metric":metric,"baseline":b,"optimized":o,"change_pct":pct})
    return rows
