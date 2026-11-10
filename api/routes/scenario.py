from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from api.schemas.scenario import ScenarioRequest, ScenarioResponse
from api.services.inventory_service import InventoryService

router = APIRouter()
_service = InventoryService()


@lru_cache(maxsize=512)
def _scenario_cached(
    store_id: str,
    item_id: str,
    service_level: float,
    lead_time_days: int,
    demand_growth: float,
):
    """Memoize repeated what-if calculations for interactive slider use."""
    base = _service.calculate(
        store_id, item_id, service_level, lead_time_days, 0.0
    )
    scenario = dict(base)
    factor = 1.0 + demand_growth
    for key in (
        "mean_daily_demand",
        "lead_time_demand",
        "safety_stock",
        "reorder_point",
        "order_quantity",
    ):
        scenario[key] = float(scenario[key]) * factor
    scenario["scenario_demand_growth"] = demand_growth
    return {"base": base, "scenario": scenario}


@router.post("/scenario", response_model=ScenarioResponse)
def scenario(req: ScenarioRequest):
    try:
        return _scenario_cached(
            str(req.store_id),
            str(req.item_id),
            round(float(req.service_level), 4),
            int(req.lead_time_days),
            round(float(req.demand_growth), 4),
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Scenario calculation failed due to an internal error.",
        ) from exc
