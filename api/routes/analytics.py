from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
_service = AnalyticsService()


def _run(call):
    try:
        return call()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Retail analytics database is temporarily unavailable.") from exc


@router.get("/overview")
def overview():
    return _run(_service.overview)


@router.get("/product-performance")
def product_performance(
    limit: int = Query(default=50, ge=1, le=200),
    sort_by: str = Query(default="total_units"),
):
    return _run(lambda: _service.product_performance(limit, sort_by))


@router.get("/seasonality")
def seasonality(store_id: str | None = None, item_id: str | None = None):
    return _run(lambda: _service.seasonality(store_id, item_id))


@router.get("/interval-evaluation")
def interval_evaluation(limit: int = Query(default=20, ge=1, le=100)):
    return _run(lambda: _service.interval_evaluation(limit))


@router.get("/inventory-sensitivity")
def inventory_sensitivity(limit: int = Query(default=100, ge=1, le=500)):
    return _run(lambda: _service.inventory_sensitivity(limit))


@router.get("/model-evaluation")
def model_evaluation(limit: int = Query(default=100, ge=1, le=500)):
    return _run(lambda: _service.model_evaluation(limit))
