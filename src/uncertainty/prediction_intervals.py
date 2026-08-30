import numpy as np

def normal_interval(forecast, residual_std: float, z: float = 1.96):
    forecast = np.asarray(forecast, dtype=float)
    margin = z * float(residual_std)
    lower = np.clip(forecast - margin, 0, None)
    upper = forecast + margin
    return lower, upper
