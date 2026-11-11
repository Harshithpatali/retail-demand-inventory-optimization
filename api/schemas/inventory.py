from pydantic import BaseModel, Field


class InventoryRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=64)
    item_id: str = Field(min_length=1, max_length=64)
    service_level: float = Field(default=0.90, gt=0.50, lt=0.999)
    lead_time_days: int = Field(default=7, ge=0, le=90)
    review_period_days: int = Field(default=7, ge=1, le=30)
    current_inventory: float = Field(default=0, ge=0, le=1_000_000)


class InventoryResponse(BaseModel):
    mean_daily_demand: float
    lead_time_demand: float
    demand_std: float
    safety_stock: float
    reorder_point: float
    target_inventory_position: float
    order_quantity: float
    service_level: float
    lead_time_days: int
    review_period_days: int
    protection_period_days: int
    current_inventory: float
    recommended_action: str
    store_id: str
    item_id: str
    model_name: str
    inventory_position_assumption: str
    demand_estimation_window_days: int
