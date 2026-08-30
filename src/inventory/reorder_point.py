from .safety_stock import safety_stock

def reorder_point(mean_daily_demand: float, sigma_daily: float, lead_time_days: int, service_level: float):
    ltd = max(0.0, mean_daily_demand) * max(0, lead_time_days)
    ss = safety_stock(max(0.0, sigma_daily), max(0, lead_time_days), service_level)
    return ltd + ss, ltd, ss
