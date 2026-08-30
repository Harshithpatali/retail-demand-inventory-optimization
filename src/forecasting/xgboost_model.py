from xgboost import XGBRegressor

def build_xgboost(cfg: dict, random_seed: int, n_jobs: int):
    p = cfg.copy()
    p["random_state"] = random_seed
    p["n_jobs"] = n_jobs
    p["tree_method"] = "hist"
    return XGBRegressor(**p)
