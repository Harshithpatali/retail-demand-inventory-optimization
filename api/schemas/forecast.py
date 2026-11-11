from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=64)
    item_id: str = Field(min_length=1, max_length=64)
    horizon_days: int = Field(default=7, ge=1, le=90)


class ForecastPoint(BaseModel):
    date: str
    forecast: float
    lower: float
    upper: float


class ForecastResponse(BaseModel):
    model_name: str
    residual_std: float
    interval_method: str = "normal_fallback"
    nominal_coverage: float = 0.90
    forecasts: list[ForecastPoint]
