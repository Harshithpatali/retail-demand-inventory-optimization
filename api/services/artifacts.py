import joblib
import pandas as pd
from src.utils.config import ROOT

class ArtifactStore:
    def __init__(self): self.root=ROOT
    def load_model(self):
        p=self.root/"models/forecasting/best_model.joblib"
        if not p.exists(): raise FileNotFoundError("Forecast failed: model artifact not found.")
        return joblib.load(p)
    def load_uncertainty(self):
        p=self.root/"models/uncertainty/residual_stats.joblib"
        if not p.exists(): raise FileNotFoundError("Forecast failed: uncertainty artifact not found.")
        return joblib.load(p)
    def load_data(self):
        p=self.root/"data/processed/forecast_features.parquet"
        if not p.exists(): raise FileNotFoundError("Forecast failed: processed features not found.")
        return pd.read_parquet(p)
