import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.forecast import router as forecast_router
from api.routes.inventory import router as inventory_router
from api.routes.scenario import router as scenario_router
from api.routes.business import router as business_router
from api.routes.options import router as options_router
from api.routes.series import router as series_router
from api.routes.eda import router as eda_router
from api.routes.network import router as network_router

app = FastAPI(
    title="Retail Demand Forecasting & Inventory Optimization API",
    version="1.2.0",
    description="Low-latency demand intelligence and inventory decision API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip().rstrip("/") for origin in os.getenv("CORS_ALLOWED_ORIGINS", "https://retail-demand-inventory-optimization-v1.streamlit.app,http://localhost:8501,http://127.0.0.1:8501").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=600,
)
for router in [
    health_router,
    forecast_router,
    inventory_router,
    scenario_router,
    business_router,
    options_router,
    series_router,
    eda_router,
    network_router,
]:
    app.include_router(router)


@app.get("/")
def root():
    """Small API landing page with links to health, network data and interactive docs."""
    return {
        "service": "Retail Demand Forecasting & Inventory Optimization API",
        "version": app.version,
        "status": "online",
        "health": "/health",
        "network_intelligence": "/network",
        "api_docs": "/docs",
        "openapi": "/openapi.json",
    }
