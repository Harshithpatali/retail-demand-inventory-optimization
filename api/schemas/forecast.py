from pydantic import BaseModel, Field
class ForecastRequest(BaseModel):
    store_id: str
    item_id: str
    horizon_days: int = Field(default=7, ge=1, le=90)
class ForecastPoint(BaseModel):
    date: str
    forecast: float
    lower: float
    upper: float
class ForecastResponse(BaseModel):
    model_name: str
    residual_std: float
    forecasts: list[ForecastPoint]
