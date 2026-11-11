# Architecture

Raw M5 CSVs -> validation and deterministic sample selection -> cleaned Parquet -> feature Parquet -> baseline/ML experiments -> out-of-sample uncertainty calibration -> validation policy optimization -> held-out inventory simulation -> business-impact reports -> FastAPI -> Streamlit.

## Live serving path

- FastAPI readiness checks verify that feature, series-options, model and uncertainty artifacts exist before Render routes traffic.
- Render regenerates the validation residual calibration artifact at build time with `python -m scripts.estimate_uncertainty`.
- Forecasts use 90% split-conformal absolute-residual intervals when calibration scores are present; older artifacts fall back to a normal approximation.
- Inventory uses one shared periodic-review `(R,S)` policy in the API and dashboard. The protection period is lead time plus the seven-day review cycle.
- The live inventory calculator uses on-hand stock as a proxy for inventory position because open purchase orders and reservations are not present in the demo input.

## Geographic path

Observed M5 store performance is aggregated to state level. Synthetic distribution-centre anchors are illustrative scenario markers only. The project does not claim actual warehouse addresses, routes, road distances or facility assignments.
