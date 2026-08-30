import pandas as pd
import numpy as np

def naive_forecast(history: pd.Series, horizon: int) -> np.ndarray:
    value = float(history.iloc[-1]) if len(history) else 0.0
    return np.repeat(value, horizon)

def seasonal_naive_forecast(history: pd.Series, horizon: int, season: int = 7) -> np.ndarray:
    if len(history) < season:
        return naive_forecast(history, horizon)
    base = history.iloc[-season:].to_numpy(dtype=float)
    return np.resize(base, horizon)

def moving_average_forecast(history: pd.Series, horizon: int, window: int = 7) -> np.ndarray:
    value = float(history.tail(window).mean()) if len(history) else 0.0
    return np.repeat(value, horizon)
