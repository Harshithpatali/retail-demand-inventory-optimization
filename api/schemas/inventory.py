from pydantic import BaseModel, Field
class InventoryRequest(BaseModel):
    store_id: str
    item_id: str
    service_level: float = Field(default=0.90, gt=0, lt=1)
    lead_time_days: int = Field(default=7, ge=0, le=90)
    current_inventory: float = Field(default=0, ge=0)
class InventoryResponse(BaseModel):
    mean_daily_demand: float
    lead_time_demand: float
    demand_std: float
    safety_stock: float
    reorder_point: float
    order_quantity: float
    service_level: float
    lead_time_days: int
    current_inventory: float
    recommended_action: str
    store_id: str
    item_id: str
    model_name: str
