import numpy as np

def residual_statistics(residuals) -> dict:
    r=np.asarray(residuals,dtype=float)
    return {"n":int(r.size),"mean":float(r.mean()) if r.size else 0.0,"std":float(r.std(ddof=1)) if r.size>1 else 0.0,"mae":float(np.mean(np.abs(r))) if r.size else 0.0,"rmse":float(np.sqrt(np.mean(r**2))) if r.size else 0.0}
