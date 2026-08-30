from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.forecast import router as forecast_router
from api.routes.inventory import router as inventory_router
from api.routes.scenario import router as scenario_router
from api.routes.business import router as business_router
from api.routes.options import router as options_router

app=FastAPI(title="Retail Demand Forecasting & Inventory Optimization API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
for router in [health_router,forecast_router,inventory_router,scenario_router,business_router,options_router]: app.include_router(router)
