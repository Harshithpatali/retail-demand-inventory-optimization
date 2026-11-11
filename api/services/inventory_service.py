from __future__ import annotations

import numpy as np

from api.services.artifacts import ArtifactStore
from src.inventory.inventory_policy import InventoryPolicy, calculate_policy


class InventoryService:
    """Shared periodic-review inventory calculator used by the live API."""

    def __init__(self):
        self.store = ArtifactStore()

    def calculate(
        self,
        store_id: str,
        item_id: str,
        service_level: float,
        lead_time_days: int,
        current_inventory: float,
        review_period_days: int = 7,
        include_model_metadata: bool = True,
    ) -> dict:
        history = self.store.load_series(store_id, item_id)
        if history.empty:
            raise ValueError("Unknown store_id/item_id combination.")

        demand = (
            np.asarray(history["demand"], dtype=float)
        )
        demand = demand[np.isfinite(demand)]
        if demand.size == 0:
            raise ValueError("No valid demand observations are available.")

        mean = float(demand.mean())
        std = float(demand.std(ddof=1)) if demand.size > 1 else 0.0
        policy = calculate_policy(
            InventoryPolicy(
                mean_daily_demand=mean,
                demand_std=std,
                lead_time_days=int(lead_time_days),
                service_level=float(service_level),
                review_period_days=int(review_period_days),
                min_order_quantity=1.0,
                max_order_quantity=500.0,
            )
        )

        target = float(policy["target_inventory_position"])
        on_hand = float(current_inventory)
        order_quantity = max(0.0, min(500.0, target - on_hand))
        action = "REORDER" if order_quantity > 0 else "HOLD"

        model_name = "not_required"
        if include_model_metadata:
            try:
                model_name = self.store.load_model()["model_name"]
            except FileNotFoundError:
                pass

        return {
            "mean_daily_demand": mean,
            "lead_time_demand": mean * int(lead_time_days),
            "demand_std": std,
            "safety_stock": float(policy["safety_stock"]),
            "reorder_point": target,
            "target_inventory_position": target,
            "order_quantity": order_quantity,
            "service_level": float(service_level),
            "lead_time_days": int(lead_time_days),
            "review_period_days": int(review_period_days),
            "protection_period_days": int(policy["protection_period_days"]),
            "current_inventory": on_hand,
            "recommended_action": action,
            "store_id": str(store_id),
            "item_id": str(item_id),
            "model_name": model_name,
            "inventory_position_assumption": "on_hand_only_no_open_purchase_orders",
            "demand_estimation_window_days": int(len(demand)),
        }
