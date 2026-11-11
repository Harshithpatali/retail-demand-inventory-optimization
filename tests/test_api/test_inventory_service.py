import pandas as pd

from api.services.inventory_service import InventoryService


class FakeArtifactStore:
    def load_series(self, store_id, item_id):
        return pd.DataFrame({"demand": [10.0] * 365})

    def load_model(self):
        return {"model_name": "test-model"}


def test_live_inventory_uses_lead_plus_review_and_orders_to_target(monkeypatch):
    service = InventoryService()
    service.store = FakeArtifactStore()

    result = service.calculate(
        store_id="CA_1",
        item_id="FOODS_2_019",
        service_level=0.90,
        lead_time_days=7,
        current_inventory=20.0,
        review_period_days=7,
        include_model_metadata=False,
    )

    assert result["protection_period_days"] == 14
    assert result["target_inventory_position"] == 140.0
    assert result["reorder_point"] == 140.0
    assert result["order_quantity"] == 120.0
    assert result["recommended_action"] == "REORDER"
    assert result["demand_estimation_window_days"] == 365
    assert result["inventory_position_assumption"] == "on_hand_only_no_open_purchase_orders"


def test_live_inventory_holds_when_on_hand_exceeds_target():
    service = InventoryService()
    service.store = FakeArtifactStore()

    result = service.calculate(
        store_id="CA_1",
        item_id="FOODS_2_019",
        service_level=0.90,
        lead_time_days=7,
        current_inventory=200.0,
        review_period_days=7,
        include_model_metadata=False,
    )

    assert result["recommended_action"] == "HOLD"
    assert result["order_quantity"] == 0.0
