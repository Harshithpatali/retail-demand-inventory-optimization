from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.services.artifacts import ArtifactStore

router = APIRouter()
_store = ArtifactStore()


@lru_cache(maxsize=256)
def _series_cached(store_id: str, item_id: str):
    """Cache the latest historical observations for repeat dashboard requests."""
    frame = _store.load_series(store_id, item_id)
    if frame.empty:
        return None

    records = []
    for row in frame.itertuples(index=False):
        price = None if pd.isna(row.sell_price) else float(row.sell_price)
        records.append({
            "date": row.date.date().isoformat(),
            "demand": float(row.demand),
            "sell_price": price,
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
