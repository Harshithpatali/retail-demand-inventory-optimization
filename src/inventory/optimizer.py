from typing import Callable
import pandas as pd
from .inventory_policy import InventoryPolicy, calculate_policy

def optimize_policy(simulator_factory: Callable[[dict], dict], mean_daily_demand: float, demand_std: float, service_levels, review_periods, lead_time_days: int, min_order: float, max_order: float) -> pd.DataFrame:
    rows=[]
    for sl in service_levels:
        for rp in review_periods:
            policy=calculate_policy(InventoryPolicy(mean_daily_demand,demand_std,lead_time_days,float(sl),int(rp),min_order,max_order))
            result=simulator_factory(policy)
            rows.append({**policy, **result})
    return pd.DataFrame(rows).sort_values(["total_cost","service_level","review_period_days"],ascending=[True,False,True]).reset_index(drop=True)
