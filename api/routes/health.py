from fastapi import APIRouter, HTTPException

from src.utils.config import ROOT

router = APIRouter()


@router.get("/health")
def health():
    """Liveness probe: the process is responding."""
    return {"status": "ok"}


@router.get("/ready")
def readiness():
    """Readiness probe used by the hosting platform before routing traffic."""
    required = {
        "features": ROOT / "data" / "processed" / "forecast_features.parquet",
        "series_options": ROOT / "data" / "processed" / "series_options.json",
        "forecast_model": ROOT / "models" / "forecasting" / "best_model.joblib",
        "uncertainty": ROOT / "models" / "uncertainty" / "residual_stats.joblib",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "missing_artifacts": missing},
        )
    return {
        "status": "ready",
        "missing_artifacts": [],
        "history_window_days": int(__import__("os").getenv("API_HISTORY_DAYS", "365")),
    }
