from __future__ import annotations

from api.services.artifacts import ArtifactStore
from src.inventory.safety_stock import safety_stock


class InventoryService:

    def __init__(self):

        self.store = ArtifactStore()

    def calculate(
        self,
        store_id,
        item_id,
        service_level,
        lead_time_days,
        current_inventory,
    ):

        history = self.store.load_series(
            store_id,
            item_id,
        )

        if history.empty:

            raise ValueError(
                "Unknown store_id/item_id combination."
            )

        demand = (
            history["demand"]
            .astype(float)
        )

        mean = float(
            demand.mean()
        )

        std = (
            float(
                demand.std(
                    ddof=1
                )
            )
            if len(demand) > 1
            else 0.0
        )

        safety = safety_stock(
            std,
            lead_time_days,
            service_level,
        )

        lead_time_demand = (
            mean
            * lead_time_days
        )

        reorder = (
            lead_time_demand
            + safety
        )

        order_quantity = max(
            1.0,
            min(
                500.0,
                mean * 7,
            ),
        )

        action = (
            "REORDER"
            if current_inventory < reorder
            else "HOLD"
        )

        model_name = "unavailable"

        try:

            model_name = self.store.load_model()[
                "model_name"
            ]

        except FileNotFoundError:

            pass

        return {
            "mean_daily_demand":
                mean,

            "lead_time_demand":
                lead_time_demand,

            "demand_std":
                std,

            "safety_stock":
                safety,

            "reorder_point":
                reorder,

            "order_quantity":
                order_quantity,

            "service_level":
                service_level,

            "lead_time_days":
                lead_time_days,

            "current_inventory":
                current_inventory,

            "recommended_action":
                action,

            "store_id":
                store_id,

            "item_id":
                item_id,

            "model_name":
                model_name,
        }