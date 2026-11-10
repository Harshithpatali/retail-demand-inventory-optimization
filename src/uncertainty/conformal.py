"""Finite-sample split-conformal calibration for forecast residuals."""
import math
import numpy as np

def conformal_quantile(scores, coverage=0.90):
    x=np.asarray(scores,dtype=float); x=x[np.isfinite(x)]
    if not len(x): raise ValueError("At least one finite calibration score is required.")
    if not 0 < coverage < 1: raise ValueError("coverage must be between 0 and 1.")
    rank=min(len(x),math.ceil((len(x)+1)*coverage))
    return float(np.partition(x,rank-1)[rank-1])

def absolute_residual_radius(residuals,coverage=0.90):
    return conformal_quantile(np.abs(np.asarray(residuals,dtype=float)),coverage)

def block_residual_scores(residuals,horizon):
    r=np.asarray(residuals,dtype=float)
    if horizon<1: raise ValueError("horizon must be >= 1.")
    n=len(r)//horizon
    return np.abs(r[:n*horizon].reshape(n,horizon).sum(axis=1)) if n else np.asarray([])

def empirical_protection_quantile(residuals,protection_days,coverage):
    scores=block_residual_scores(residuals,protection_days)
    if scores.size: return conformal_quantile(scores,coverage)
    return absolute_residual_radius(residuals,coverage)*math.sqrt(protection_days)

def interval_bounds(predictions,residuals,coverage=0.90):
    radius=absolute_residual_radius(residuals,coverage); p=np.asarray(predictions,dtype=float)
    return np.maximum(0,p-radius),np.maximum(0,p+radius)
