from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.services.statistical_service import StatisticalService

router = APIRouter(prefix="/statistics", tags=["statistics"])
_service = StatisticalService()


@router.get("/series")
def series_statistics(store_id: str, item_id: str):
    try:
        return _service.analyze(str(store_id), str(item_id))
    except ValueError as exc:
        status = 404 if "Unknown store_id/item_id" in str(exc) else 422
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
