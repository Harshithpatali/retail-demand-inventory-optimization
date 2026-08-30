import joblib
from src.utils.config import ROOT
class BusinessService:
    def get(self):
        p=ROOT/"models/uncertainty/business_metrics.joblib"
        if not p.exists(): return {"available":False,"metrics":[],"notes":"Business-impact artifacts are not available yet. Run python -m scripts.run_inventory_simulation and python -m scripts.build_business_impact."}
        s=joblib.load(p)
        return {"available":True,"metrics":s,"notes":"Metrics are simulation results based on configured cost assumptions."}
