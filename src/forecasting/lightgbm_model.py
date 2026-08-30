from lightgbm import LGBMRegressor

def build_lightgbm(cfg: dict, random_seed: int, n_jobs: int):
    return LGBMRegressor(random_state=random_seed, n_jobs=n_jobs, verbosity=-1, **cfg)
