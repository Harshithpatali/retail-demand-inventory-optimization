# Model card

Models: XGBoost and LightGBM global regressors. Primary selection metric: validation WAPE among ML candidates. Data split is chronological. Training features exclude future target values through shifted lags and rolling windows. Residual uncertainty is based on out-of-sample validation predictions.

Known limitations: the local experiment intentionally uses a subset of M5; forecast price/event inputs for future API horizons are carried forward or defaulted where future information is unavailable; cost assumptions are illustrative.


## Live forecast uncertainty

The forecast API uses a split-conformal absolute-residual radius calibrated on out-of-sample validation residuals when `calibration_abs_residuals` are present in the uncertainty artifact. The nominal live interval is 90%. If an older artifact lacks those residuals, the service explicitly reports and uses a normal-approximation fallback. Time dependence and distribution shift mean empirical validation coverage is not a future guarantee.

Regenerate the calibration artifact after retraining:

```bash
python -m scripts.train_models
python -m scripts.estimate_uncertainty
```
