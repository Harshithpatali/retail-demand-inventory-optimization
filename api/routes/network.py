from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.services.artifacts import ArtifactStore

router = APIRouter()
_store = ArtifactStore()

STATE_NAMES = {
    "CA": "California",
    "TX": "Texas",
    "WI": "Wisconsin",
}

# These are scenario anchors only. They are not verified warehouse locations.
SYNTHETIC_CENTERS = [
    {
        "distribution_center_id": "SYNTH_DC_CA",
        "state_code": "CA",
        "state_name": "California",
        "city_label": "Los Angeles area (synthetic)",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "location_type": "synthetic_scenario_anchor",
    },
    {
        "distribution_center_id": "SYNTH_DC_TX",
        "state_code": "TX",
        "state_name": "Texas",
        "city_label": "Dallas area (synthetic)",
        "latitude": 32.7767,
        "longitude": -96.7970,
        "location_type": "synthetic_scenario_anchor",
    },
    {
        "distribution_center_id": "SYNTH_DC_WI",
        "state_code": "WI",
        "state_name": "Wisconsin",
        "city_label": "Milwaukee area (synthetic)",
        "latitude": 43.0389,
        "longitude": -87.9065,
        "location_type": "synthetic_scenario_anchor",
    },
]


@lru_cache(maxsize=1)
def _network_payload(parquet_path: str):
    """Aggregate the selected M5 sample once per API worker."""
    frame = pd.read_parquet(
        parquet_path,
        columns=["id", "date", "demand", "store_id", "item_id", "state_code"],
    )
    if frame.empty:
        return None

    frame["store_id"] = frame["store_id"].astype(str)
    frame["state_code"] = frame["state_code"].astype(str)
    frame["demand"] = pd.to_numeric(frame["demand"], errors="coerce").fillna(0.0)

    daily_store = (
        frame.groupby(["store_id", "state_code", "date"], observed=True)["demand"]
        .sum()
        .reset_index()
    )
    store_metrics = (
        frame.groupby(["store_id", "state_code"], observed=True)
        .agg(
            total_demand=("demand", "sum"),
            series_count=("id", "nunique"),
            item_count=("item_id", "nunique"),
        )
        .reset_index()
    )
    run_rates = (
        daily_store.groupby(["store_id", "state_code"], observed=True)["demand"]
        .mean()
        .rename("average_daily_demand")
        .reset_index()
    )
    store_metrics = store_metrics.merge(
        run_rates, on=["store_id", "state_code"], how="left"
    )

    stores = []
    for row in store_metrics.sort_values(["state_code", "store_id"]).itertuples(index=False):
        state_code = str(row.state_code)
        stores.append({
            "store_id": str(row.store_id),
            "state_code": state_code,
            "state_name": STATE_NAMES.get(state_code, state_code),
            "total_demand": float(row.total_demand),
            "average_daily_demand": float(row.average_daily_demand),
            "series_count": int(row.series_count),
            "item_count": int(row.item_count),
            "distribution_center_id": f"SYNTH_DC_{state_code}",
            "assignment_type": "synthetic_state_match",
        })

    store_frame = pd.DataFrame(stores)
    states = (
        store_frame.groupby(["state_code", "state_name"], observed=True)
        .agg(
            total_demand=("total_demand", "sum"),
            average_daily_demand=("average_daily_demand", "sum"),
            store_count=("store_id", "nunique"),
            series_count=("series_count", "sum"),
            item_count=("item_count", "sum"),
        )
        .reset_index()
    )
    state_records = [
        {
            "state_code": str(row.state_code),
            "state_name": str(row.state_name),
            "total_demand": float(row.total_demand),
            "average_daily_demand": float(row.average_daily_demand),
            "store_count": int(row.store_count),
            "series_count": int(row.series_count),
            "item_count": int(row.item_count),
        }
        for row in states.itertuples(index=False)
    ]
    return {
        "states": state_records,
        "stores": stores,
        "distribution_centers": SYNTHETIC_CENTERS,
        "metadata": {
            "store_location_precision": "state_level_only",
            "distribution_center_locations": "synthetic_scenario_anchors",
            "store_assignment": "synthetic_state_match",
            "road_distances_available": False,
            "source": "M5 selected store-item historical demand sample",
            "observations": int(len(frame)),
            "start_date": pd.to_datetime(frame["date"]).min().date().isoformat(),
            "end_date": pd.to_datetime(frame["date"]).max().date().isoformat(),
        },
    }


@router.get("/network")
def network():
    """State-level M5 store analytics plus clearly labelled synthetic DC scenarios."""
    try:
        path = _store._features_path()
        payload = _network_payload(path)
        if payload is None:
            raise HTTPException(status_code=404, detail="No network data available.")
        return payload
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
