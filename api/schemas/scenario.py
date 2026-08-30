from pydantic import BaseModel, Field
from .inventory import InventoryResponse
class ScenarioRequest(BaseModel):
    store_id: str
    item_id: str
    service_level: float = Field(default=0.90, gt=0, lt=1)
    lead_time_days: int = Field(default=7, ge=0, le=90)
    demand_growth: float = Field(default=0.0, ge=-0.9, le=5.0)
class ScenarioResponse(BaseModel):
    base: dict
    scenario: dict
