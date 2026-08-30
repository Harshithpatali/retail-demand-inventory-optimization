from fastapi import APIRouter, HTTPException
from api.schemas.forecast import ForecastRequest, ForecastResponse, ForecastPoint
from api.services.forecast_service import ForecastService
router=APIRouter()
@router.post("/forecast",response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    try:
        name,std,out=ForecastService().forecast(req.store_id,req.item_id,req.horizon_days)
        return ForecastResponse(model_name=name,residual_std=std,forecasts=[ForecastPoint(date=str(r.date.date()),forecast=float(r.forecast),lower=float(r.lower),upper=float(r.upper)) for _,r in out.iterrows()])
    except (FileNotFoundError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))
    except Exception: raise HTTPException(status_code=500,detail="Forecast failed due to an internal error.")
