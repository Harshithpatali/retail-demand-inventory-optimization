from __future__ import annotations

import numpy as np
import pandas as pd

from api.services.artifacts import ArtifactStore


class StatisticalService:
    """Small-sample-safe time-series diagnostics for a selected item-store series."""

    def __init__(self):
        self.store = ArtifactStore()

    @staticmethod
    def _block_bootstrap_mean(values: np.ndarray, block_size: int = 7,
                              repetitions: int = 1000, seed: int = 2026) -> tuple[float, float]:
        n = len(values)
        if n < 14:
            return float(np.mean(values)), float(np.mean(values))
        rng = np.random.default_rng(seed)
        starts = np.arange(max(1, n - block_size + 1))
        blocks_needed = int(np.ceil(n / block_size))
        estimates = np.empty(repetitions, dtype=float)
        for i in range(repetitions):
            chosen = rng.choice(starts, size=blocks_needed, replace=True)
            sample = np.concatenate([values[s:s + block_size] for s in chosen])[:n]
            estimates[i] = sample.mean()
        return tuple(float(v) for v in np.quantile(estimates, [0.025, 0.975]))

    @staticmethod
    def _weekday_permutation(frame: pd.DataFrame, repetitions: int = 999,
                             seed: int = 2026) -> dict:
        # Permute weekday labels within calendar weeks, preserving each week's
        # demand vector and its serial dependence structure.
        x = frame[["date", "demand"]].copy()
        x["weekday"] = pd.to_datetime(x["date"]).dt.weekday
        x["week"] = (pd.to_datetime(x["date"]) - pd.to_timedelta(x["weekday"], unit="D")).dt.date
        pivot = x.pivot_table(index="week", columns="weekday", values="demand", aggfunc="mean")
        pivot = pivot.reindex(columns=range(7)).dropna()
        if len(pivot) < 8:
            return {"statistic": None, "p_value": None, "weeks": int(len(pivot)),
                    "method": "within-week weekday-label permutation; insufficient complete weeks"}
        matrix = pivot.to_numpy(dtype=float)
        observed = matrix.mean(axis=0)
        statistic = float(observed.max() - observed.min())
        rng = np.random.default_rng(seed)
        exceed = 0
        for _ in range(repetitions):
            permuted = np.vstack([row[rng.permutation(7)] for row in matrix])
            score = float(permuted.mean(axis=0).max() - permuted.mean(axis=0).min())
            exceed += score >= statistic
        return {"statistic": statistic, "p_value": float((exceed + 1) / (repetitions + 1)),
                "weeks": int(len(pivot)),
                "method": "within-week weekday-label permutation (complete weeks only)"}

    def analyze(self, store_id: str, item_id: str) -> dict:
        frame = self.store.load_full_series(store_id, item_id)
        if frame.empty:
            raise ValueError("Unknown store_id/item_id combination.")
        frame = frame[["date", "demand"]].copy().sort_values("date")
        frame["date"] = pd.to_datetime(frame["date"])
        values = pd.to_numeric(frame["demand"], errors="coerce").dropna().to_numpy(dtype=float)
        if len(values) < 14:
            raise ValueError("At least 14 daily observations are required for the statistical laboratory.")
        mean = float(values.mean())
        std = float(values.std(ddof=1))
        lower, upper = self._block_bootstrap_mean(values)
        weekly = self._weekday_permutation(frame)
        return {
            "store_id": store_id, "item_id": item_id,
            "observations": int(len(values)),
            "mean_daily_demand": mean, "median_daily_demand": float(np.median(values)),
            "std_daily_demand": std, "variance_daily_demand": float(np.var(values, ddof=1)),
            "coefficient_of_variation": float(std / mean) if mean else None,
            "zero_demand_rate": float(np.mean(values == 0)),
            "intermittency_mean_interval": float(len(values) / max(1, np.count_nonzero(values))),
            "mean_95pct_block_bootstrap_ci": [lower, upper],
            "weekday_effect_test": weekly,
            "inference_notes": [
                "Mean-demand interval uses a 7-day moving-block bootstrap to retain short-range serial dependence.",
                "Weekday test permutes weekday labels within complete calendar weeks; interpret as exploratory.",
                "M5 is observational competition data, not a randomized retail experiment."
            ]
        }
