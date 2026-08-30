def demand_cover_order_quantity(mean_daily_demand: float, cover_days: int, min_order: float, max_order: float) -> float:
    raw = max(0.0, mean_daily_demand) * max(1, int(cover_days))
    return float(min(max(raw, min_order), max_order))
