from fastapi import APIRouter, HTTPException
from api.schemas.scenario import ScenarioRequest, ScenarioResponse
from api.services.inventory_service import InventoryService
router=APIRouter()
@router.post("/scenario",response_model=ScenarioResponse)
def scenario(req: ScenarioRequest):
    try:
        service=InventoryService(); base=service.calculate(req.store_id,req.item_id,req.service_level,req.lead_time_days,0.0); growth=req.demand_growth
        scenario=dict(base); scenario["mean_daily_demand"]*=1+growth; scenario["lead_time_demand"]*=1+growth; scenario["safety_stock"]*=1+growth; scenario["reorder_point"]*=1+growth; scenario["order_quantity"]*=1+growth; scenario["scenario_demand_growth"]=growth
        return {"base":base,"scenario":scenario}
    except (FileNotFoundError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))
    except Exception: raise HTTPException(status_code=500,detail="Scenario calculation failed due to an internal error.")
