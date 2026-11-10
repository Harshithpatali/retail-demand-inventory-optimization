from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from api.services.artifacts import ArtifactStore

router = APIRouter()
_store = ArtifactStore()


@lru_cache(maxsize=256)
def _series_cached(store_id: str, item_id: str):
    frame = _store.load_series(store_id, item_id)
    if frame.empty:
        return None
    # Return immutable, JSON-safe records from the cached dataframe.
    records = []
    for row in frame.itertuples(index=False):
        records.append({
            "date": row.date.date().isoformat(),
            "demand": float(row.demand),
            "sell_price": (
                float(row.sell_price)
                if row.sell_price is not None
                else None
            ),
        })
    return tuple(records)


@router.get("/series")
def series(store_id: str, item_id: str):
    """Return the latest cached history for one store-item series."""
    try:
        records = _series_cached(str(store_id), str(item_id))
        if records is None:
            raise HTTPException(
                status_code=404,
                detail="Unknown store_id/item_id combination.",
            )
        return {
            "store_id": str(store_id),
            "item_id": str(item_id),
            "history": list(records),
            "observations": len(records),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
