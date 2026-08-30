from dataclasses import dataclass
from typing import Dict
from .safety_stock import safety_stock

@dataclass(frozen=True)
class InventoryPolicy:
    mean_daily_demand: float
    demand_std: float
    lead_time_days: int
    service_level: float
    review_period_days: int
    min_order_quantity: float = 1.0
    max_order_quantity: float = 500.0

def calculate_policy(p: InventoryPolicy) -> Dict[str, float]:
    if p.mean_daily_demand < 0 or p.demand_std < 0: raise ValueError("Demand statistics must be non-negative.")
    if p.lead_time_days < 0: raise ValueError("lead_time_days must be non-negative.")
    if p.review_period_days < 1: raise ValueError("review_period_days must be at least 1.")
    if not 0 < p.service_level < 1: raise ValueError("service_level must be between 0 and 1.")
    protection = p.lead_time_days + p.review_period_days
    ss = safety_stock(p.demand_std, protection, p.service_level)
    target = max(0.0, p.mean_daily_demand * protection + ss)
    return {
        "mean_daily_demand": float(p.mean_daily_demand),
        "demand_std": float(p.demand_std),
        "lead_time_days": int(p.lead_time_days),
        "review_period_days": int(p.review_period_days),
        "protection_period_days": int(protection),
        "service_level": float(p.service_level),
        "safety_stock": float(ss),
        "target_inventory_position": float(target),
        "reorder_point": float(target),
        "min_order_quantity": float(p.min_order_quantity),
        "max_order_quantity": float(p.max_order_quantity),
    }
