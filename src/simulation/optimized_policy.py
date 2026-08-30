def optimized_policy(policy: dict) -> dict:
    required={"service_level","review_period_days","target_inventory_position","lead_time_days","min_order_quantity","max_order_quantity"}
    missing=required-set(policy)
    if missing: raise ValueError(f"Optimized policy missing fields: {sorted(missing)}")
    return dict(policy)
