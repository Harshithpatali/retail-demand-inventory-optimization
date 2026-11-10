from functools import lru_cache

from fastapi import APIRouter, HTTPException

from api.schemas.forecast import ForecastRequest, ForecastResponse, ForecastPoint
from api.services.forecast_service import ForecastService

router = APIRouter()
_service = ForecastService()


@lru_cache(maxsize=256)
def _forecast_cached(store_id: str, item_id: str, horizon_days: int):
    """Cache repeat forecasts; model and series artifacts are cached separately."""
    name, std, output = _service.forecast(store_id, item_id, horizon_days)
    points = [
        {
            "date": str(row.date.date()),
            "forecast": float(row.forecast),
            "lower": float(row.lower),
            "upper": float(row.upper),
        }
        for row in output.itertuples(index=False)
    ]
    return name, float(std), points


@router.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    try:
        name, std, points = _forecast_cached(
            req.store_id,
            req.item_id,
            req.horizon_days,
        )
        return ForecastResponse(
            model_name=name,
            residual_std=std,
            forecasts=[ForecastPoint(**point) for point in points],
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Forecast failed due to an internal error.",
        ) from exc
