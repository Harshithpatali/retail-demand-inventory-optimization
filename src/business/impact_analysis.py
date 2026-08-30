def impact_summary(baseline: dict, optimized: dict) -> dict:
    return {k: {"baseline": baseline[k], "optimized": optimized[k], "change_pct": ((optimized[k]-baseline[k])/baseline[k]*100 if baseline[k] else None)} for k in baseline}
