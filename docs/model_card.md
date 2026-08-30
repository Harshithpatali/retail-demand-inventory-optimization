# Model card

Models: XGBoost and LightGBM global regressors. Primary selection metric: validation WAPE among ML candidates. Data split is chronological. Training features exclude future target values through shifted lags and rolling windows. Residual uncertainty is based on out-of-sample validation predictions.

Known limitations: the local experiment intentionally uses a subset of M5; forecast price/event inputs for future API horizons are carried forward or defaulted where future information is unavailable; cost assumptions are illustrative.
