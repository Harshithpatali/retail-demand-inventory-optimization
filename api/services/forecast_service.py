from __future__ import annotations

import pandas as pd

from api.services.artifacts import ArtifactStore
from src.forecasting.predict import recursive_global_forecast
from src.uncertainty.prediction_intervals import normal_interval


class ForecastService:

    def __init__(self):

        self.store = ArtifactStore()

    def forecast(
        self,
        store_id: str,
        item_id: str,
        horizon_days: int,
    ):

        history = self.store.load_series(
            store_id,
            item_id,
        )

        if history.empty:

            raise ValueError(
                "Unknown store_id/item_id combination."
            )

        bundle = dict(
            self.store.load_model()
        )

        stats = (
            self.store.load_uncertainty()
        )

        future = pd.date_range(
            history["date"].max()
            + pd.Timedelta(days=1),
            periods=horizon_days,
            freq="D",
        )

        last = history.iloc[-1]

        for key in [
            "store_code",
            "item_code",
            "dept_code",
            "cat_code",
            "state_code",
        ]:

            bundle[key] = int(
                last[key]
            )

        output = recursive_global_forecast(
            bundle,
            history,
            future,
        )

        lower, upper = normal_interval(
            output["forecast"],
            stats["std"],
        )

        output["lower"] = lower
        output["upper"] = upper

        return (
            bundle["model_name"],
            float(stats["std"]),
            output,
        )