from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from api.services.population_analytics_service import PopulationAnalyticsService
router=APIRouter(prefix="/population",tags=["full-population R2 analytics"])
_service=PopulationAnalyticsService()
def _call(fn):
    try: return fn()
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=503,detail="Full-population R2 analytics are temporarily unavailable.") from exc
@router.get("/status")
def status(): return _call(_service.status)
@router.get("/overview")
def overview(): return _call(_service.overview)
@router.get("/segments/{dimension}")
def segments(dimension:str): return _call(lambda:_service.segments(dimension))
@router.get("/series")
def series(limit:int=Query(default=100,ge=1,le=500),offset:int=Query(default=0,ge=0),
           store_id:str|None=None,state_id:str|None=None,cat_id:str|None=None,dept_id:str|None=None,
           sort_by:str=Query(default="total_units")):
    return _call(lambda:_service.series(limit,offset,store_id,state_id,cat_id,dept_id,sort_by))
@router.get("/daily")
def daily(): return _call(_service.daily)

@router.get("/forecast/status")
def forecast_status(): return _call(_service.forecast_status)
@router.get("/forecast/metrics")
def forecast_metrics(): return _call(_service.forecast_metrics)
@router.get("/forecast/sample-comparison")
def forecast_sample_comparison(): return _call(_service.forecast_sample_comparison)
