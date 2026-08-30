from statistics import NormalDist
import math

def safety_stock(sigma_daily: float, protection_period_days: int, service_level: float) -> float:
    if sigma_daily < 0: raise ValueError("sigma_daily must be non-negative")
    if protection_period_days < 0: raise ValueError("protection_period_days must be non-negative")
    if not 0 < service_level < 1: raise ValueError("service_level must be between 0 and 1")
    z = NormalDist().inv_cdf(service_level)
    return max(0.0, z * sigma_daily * math.sqrt(protection_period_days))
