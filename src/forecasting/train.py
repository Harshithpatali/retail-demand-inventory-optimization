from dataclasses import dataclass
import pandas as pd
from src.forecasting.xgboost_model import build_xgboost
from src.forecasting.lightgbm_model import build_lightgbm
from src.forecasting.evaluate import evaluate

@dataclass
class TrainedModel:
    name: str
    model: object
    metrics: dict
    feature_columns: list[str]

def train_candidates(train_df, val_df, feature_columns, model_cfg):
    X_train, y_train = train_df[feature_columns], train_df["demand"]
    X_val, y_val = val_df[feature_columns], val_df["demand"]
    candidates=[]
    for name, builder, cfg in [
        ("xgboost", build_xgboost, model_cfg["xgboost"]),
        ("lightgbm", build_lightgbm, model_cfg["lightgbm"]),
    ]:
        model = builder(cfg, model_cfg["random_seed"], model_cfg["n_jobs"])
        model.fit(X_train, y_train)
        pred = model.predict(X_val)
        pred = pred.clip(min=0)
        candidates.append(TrainedModel(name, model, evaluate(y_val, pred), feature_columns))
    return candidates
