from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.services.inventory_scenario_service import InventoryScenarioService

router = APIRouter(prefix="/analytics", tags=["analytics"])
_service = InventoryScenarioService()


class InventoryScenarioRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=64)
    item_id: str = Field(min_length=1, max_length=64)
    current_inventory: float = Field(ge=0, le=1_000_000)
    lead_time_days: int = Field(ge=0, le=90)
    review_period_days: int = Field(default=7, ge=1, le=30)
    service_level: float = Field(gt=0.5, lt=0.999)
    unit_holding_cost: float = Field(default=0, ge=0)
    ordering_cost: float = Field(default=0, ge=0)
    stockout_cost: float = Field(default=0, ge=0)


@router.post("/inventory-scenarios")
def save_inventory_scenario(req: InventoryScenarioRequest):
    try:
        return _service.save(req.model_dump())
    except ValueError as exc:
        status = 404 if "Unknown store_id/item_id" in str(exc) else 422
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not save inventory scenario.") from exc
