from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from src.utils.config import ROOT


router = APIRouter()


OPTIONS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "series_options.json"
)


@router.get("/options")
def options():
    """Return available store/item combinations.

    This endpoint intentionally uses the tiny JSON artifact instead
    of loading the full forecast feature parquet into memory.
    """

    if not OPTIONS_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Deployment artifact missing: "
                "data/processed/series_options.json"
            ),
        )

    try:
        with OPTIONS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Options unavailable: {exc}",
        ) from exc