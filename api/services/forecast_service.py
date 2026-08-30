import pandas as pd
from src.forecasting.predict import recursive_global_forecast
from src.uncertainty.prediction_intervals import normal_interval
from api.services.artifacts import ArtifactStore

class ForecastService:
    def __init__(self): self.store=ArtifactStore()
    def forecast(self,store_id,item_id,horizon_days):
        df=self.store.load_data(); mask=(df.store_id.astype(str)==str(store_id))&(df.item_id.astype(str)==str(item_id)); g=df[mask].sort_values("date")
        if g.empty: raise ValueError("Unknown store_id/item_id combination.")
        bundle=self.store.load_model(); stats=self.store.load_uncertainty(); future=pd.date_range(g.date.max()+pd.Timedelta(days=1),periods=horizon_days,freq="D")
        b=dict(bundle); last=g.iloc[-1]
        for key in ["store_code","item_code","dept_code","cat_code","state_code"]: b[key]=int(last[key])
        out=recursive_global_forecast(b,g.tail(56),future); lo,hi=normal_interval(out.forecast,stats["std"]); out["lower"]=lo; out["upper"]=hi
        return bundle["model_name"],float(stats["std"]),out
