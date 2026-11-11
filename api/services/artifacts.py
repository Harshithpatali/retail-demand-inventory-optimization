from __future__ import annotations

from functools import lru_cache

import joblib
import pandas as pd

from src.utils.config import ROOT


SERIES_COLUMNS = [
    "id", "date", "demand", "sell_price", "store_id", "item_id",
    "store_code", "item_code", "dept_code", "cat_code", "state_code",
]


class ArtifactStore:
    """Memory-conscious, process-local cached access to model and data artifacts."""

    def __init__(self):
        self.root = ROOT

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model_cached(path: str):
        return joblib.load(path)

    def load_model(self):
        path = self.root / "models" / "forecasting" / "best_model.joblib"
        if not path.exists():
            raise FileNotFoundError("Forecast failed: model artifact not found.")
        return self._load_model_cached(str(path.resolve()))

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_uncertainty_cached(path: str):
        return joblib.load(path)

    def load_uncertainty(self):
        path = self.root / "models" / "uncertainty" / "residual_stats.joblib"
        if not path.exists():
            raise FileNotFoundError("Forecast failed: uncertainty artifact not found.")
        return self._load_uncertainty_cached(str(path.resolve()))

    @staticmethod
    @lru_cache(maxsize=256)
    def _load_series_cached(parquet_path: str, store_id: str, item_id: str) -> pd.DataFrame:
        df = pd.read_parquet(
            parquet_path,
            columns=SERIES_COLUMNS,
            filters=[("store_id", "==", store_id), ("item_id", "==", item_id)],
        )
        if df.empty:
            return df
        # Retain a year of observations for stable inventory statistics and
        # enough lag history for recursive forecasts. EDA has its own full-history loader.
        import os
        history_days = max(56, min(int(os.getenv("API_HISTORY_DAYS", "365")), 1825))
        return df.sort_values("date").tail(history_days).reset_index(drop=True)

    @staticmethod
    @lru_cache(maxsize=64)
    def _load_full_series_cached(parquet_path: str, store_id: str, item_id: str) -> pd.DataFrame:
        """Full item-store history for EDA; bounded cache prevents unbounded memory growth."""
        df = pd.read_parquet(
            parquet_path,
            columns=SERIES_COLUMNS,
            filters=[("store_id", "==", store_id), ("item_id", "==", item_id)],
        )
        if df.empty:
            return df
        return df.sort_values("date").reset_index(drop=True)

    def _features_path(self):
        path = self.root / "data" / "processed" / "forecast_features.parquet"
        if not path.exists():
            raise FileNotFoundError("Processed forecast features not found.")
        return str(path.resolve())

    def load_series(self, store_id: str, item_id: str) -> pd.DataFrame:
        return self._load_series_cached(self._features_path(), str(store_id), str(item_id))

    def load_full_series(self, store_id: str, item_id: str) -> pd.DataFrame:
        return self._load_full_series_cached(self._features_path(), str(store_id), str(item_id))
