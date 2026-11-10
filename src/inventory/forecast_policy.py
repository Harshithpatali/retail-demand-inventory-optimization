"""Forecast-driven periodic-review inventory targets."""
def calculate_forecast_target(forecast_demand,calibration_residuals,lead_time_days,review_period_days,service_level,min_order_quantity=1.0,max_order_quantity=500.0):
    import numpy as np
    from src.uncertainty.conformal import empirical_protection_quantile
    protection=int(lead_time_days)+int(review_period_days)
    if lead_time_days<0 or review_period_days<1: raise ValueError("Invalid lead/review period.")
    if not 0<service_level<1: raise ValueError("service_level must be between 0 and 1.")
    f=np.asarray(forecast_demand,dtype=float)
    if len(f)<protection: raise ValueError("Forecast must cover the full protection period.")
    if not np.all(np.isfinite(f[:protection])): raise ValueError("Forecast contains non-finite values.")
    demand=float(np.maximum(f[:protection],0).sum())
    safety=float(empirical_protection_quantile(calibration_residuals,protection,service_level))
    target=max(0.0,demand+safety)
    return {"lead_time_days":int(lead_time_days),"review_period_days":int(review_period_days),"protection_period_days":protection,"service_level":float(service_level),"forecast_protection_demand":demand,"safety_stock":safety,"target_inventory_position":target,"reorder_point":target,"min_order_quantity":float(min_order_quantity),"max_order_quantity":float(max_order_quantity),"uncertainty_method":"empirical_block_conformal"}
