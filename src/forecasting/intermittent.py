"""Croston and SBA intermittent-demand baselines."""
import numpy as np

def croston_forecast(history,horizon,alpha=0.1,sba=False):
    y=np.asarray(history,dtype=float)
    if horizon<1 or not 0<alpha<=1: raise ValueError("Invalid horizon or alpha.")
    y=np.maximum(np.where(np.isfinite(y),y,0.0),0.0); nz=np.flatnonzero(y>0)
    if not len(nz): value=0.0
    else:
        first=int(nz[0]); size=float(y[first]); interval=float(first+1); last=first
        for t in nz[1:]:
            gap=int(t-last); size=alpha*float(y[t])+(1-alpha)*size
            interval=alpha*gap+(1-alpha)*interval; last=int(t)
        value=size/max(interval,1e-12)
        if sba: value*=1-alpha/2
    return np.full(horizon,max(0.0,value),dtype=float)
