from __future__ import annotations

from functools import lru_cache

import joblib
import pandas as pd

from src.utils.config import ROOT


class ArtifactStore:
    """Memory-conscious artifact access for the API."""

    def __init__(self):
        self.root = ROOT

    # ---------------------------------------------------------------
    # MODEL
    # ---------------------------------------------------------------

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model_cached(
        path: str,
    ):
        return joblib.load(path)

    def load_model(self):

        path = (
            self.root
            / "models"
            / "forecasting"
            / "best_model.joblib"
        )

        if not path.exists():

            raise FileNotFoundError(
                "Forecast failed: model artifact not found."
            )

        return self._load_model_cached(
            str(path.resolve())
        )

    # ---------------------------------------------------------------
    # UNCERTAINTY
    # ---------------------------------------------------------------

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_uncertainty_cached(
        path: str,
    ):
        return joblib.load(path)

    def load_uncertainty(self):

        path = (
            self.root
            / "models"
            / "uncertainty"
            / "residual_stats.joblib"
        )

        if not path.exists():

            raise FileNotFoundError(
                "Forecast failed: uncertainty artifact not found."
            )

        return self._load_uncertainty_cached(
            str(path.resolve())
        )

    # ---------------------------------------------------------------
    # SERIES HISTORY
    # ---------------------------------------------------------------

    @staticmethod
    @lru_cache(maxsize=256)
    def _load_series_cached(
        parquet_path: str,
        store_id: str,
        item_id: str,
    ) -> pd.DataFrame:

        columns = [
            "id",
            "date",
            "demand",
            "sell_price",
            "store_id",
            "item_id",
            "store_code",
            "item_code",
            "dept_code",
            "cat_code",
            "state_code",
        ]

        df = pd.read_parquet(
            parquet_path,
            columns=columns,
            filters=[
                ("store_id", "==", store_id),
                ("item_id", "==", item_id),
            ],
        )

        if df.empty:
            return df

        return (
            df.sort_values("date")
            .tail(56)
            .reset_index(drop=True)
        )

    def load_series(
        self,
        store_id: str,
        item_id: str,
    ) -> pd.DataFrame:

        path = (
            self.root
            / "data"
            / "processed"
            / "forecast_features.parquet"
        )

        if not path.exists():

            raise FileNotFoundError(
                "Forecast failed: processed features not found."
            )

        return self._load_series_cached(
            str(path.resolve()),
            str(store_id),
            str(item_id),
        )