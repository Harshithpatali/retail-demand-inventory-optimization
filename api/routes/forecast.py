from functools import lru_cache

from fastapi import APIRouter, HTTPException

from api.schemas.forecast import ForecastRequest, ForecastResponse, ForecastPoint
from api.services.forecast_service import ForecastService

router = APIRouter()
_service = ForecastService()


@lru_cache(maxsize=256)
def _forecast_cached(store_id: str, item_id: str, horizon_days: int):
    """Cache repeat forecasts and their calibration metadata."""
    name, std, output, interval_method = _service.forecast(
        store_id, item_id, horizon_days
    )
    points = [
        {
            "date": str(row.date.date()),
            "forecast": float(row.forecast),
            "lower": float(row.lower),
            "upper": float(row.upper),
        }
        for row in output.itertuples(index=False)
    ]
    return name, float(std), points, interval_method


@router.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    try:
        name, std, points, interval_method = _forecast_cached(
            req.store_id, req.item_id, req.horizon_days
        )
        return ForecastResponse(
            model_name=name,
            residual_std=std,
            interval_method=interval_method,
            nominal_coverage=0.90,
            forecasts=[ForecastPoint(**point) for point in points],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if "Unknown store_id/item_id" in str(exc) else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Forecast failed due to an internal error.",
        ) from exc
