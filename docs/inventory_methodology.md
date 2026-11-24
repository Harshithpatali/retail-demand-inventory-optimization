# Inventory methodology

## Scope

This document covers both the interactive single-item inventory calculator and the offline historical policy simulation. They share the periodic-review concept but are not the same evaluation.

## Interactive API and dashboard policy

The interactive inventory endpoint and dashboard use the periodic-review `(R,S)` calculation implemented in `src/inventory/inventory_policy.py`.

- Demand statistics use the most recent 365 observations by default (configurable with `API_HISTORY_DAYS`, bounded to 56–1,825 days).
- Review period defaults to 7 days.
- Protection period is lead time plus review period.
- Target inventory position is expected protection-period demand plus safety stock.
- Safety stock uses a normal-demand approximation: `z(service level) × daily demand standard deviation × sqrt(lead time + review period)`.
- Suggested order quantity is the positive gap between target inventory position and entered on-hand quantity, capped at 500 units.
- The live interface treats on-hand stock as inventory position because open purchase orders and reservations are not present. This is an explicit simplifying assumption, not a complete ERP inventory-position calculation.

The live API and dashboard expose protection-period length, target inventory position and demand-history window so users can inspect the assumptions.

## Offline forecast-driven policy

The offline forecast policy is implemented in `src/inventory/forecast_policy.py`.

1. Compute protection period as lead time + review period.
2. Sum non-negative forecast demand over the complete protection period.
3. Estimate safety stock from historical calibration residuals using an empirical block-conformal protection-period quantile.
4. Set target inventory position to forecast protection-period demand + safety stock.
5. During validation, compare configured service-level and review-period candidates by simulated cost.
6. Freeze the selected policy and evaluate it on the final held-out demand period.

The policy uses calibration residuals from an earlier chronological validation segment; the same observations are not reused for policy selection. Test demand is used only for scoring.

## Configured simulation parameters

See `configs/inventory_config.yaml`.

| Parameter | Configured value |
|---|---:|
| Holding cost per unit-day | 0.05 |
| Fixed ordering cost per order | 5.00 |
| Stockout penalty per unmet unit | 2.00 |
| Baseline service target | 80% |
| Default service target | 90% |
| Baseline/default lead time | 7 days |
| Baseline/default review period | 7 days |
| Demand history window | 365 days |
| Minimum order quantity | 5 |
| Maximum order quantity | 500 |

These cost values are abstract simulation units. The M5 data does not provide retailer-specific costs or a currency denomination.

## Cost and service metrics

The simulator compares policies against the same held-out demand sequence. Total simulated cost combines:
- Holding cost for inventory carried over time.
- Fixed ordering cost each time a replenishment order is placed.
- Stockout penalty for each unit of unmet demand.

Stockout units count unmet demand. Fill rate measures the proportion of demand fulfilled. Average inventory describes inventory carried during the simulation. These are simulation outputs, not audited operational KPIs.

## Important differences and limitations

- The offline historical-demand baseline and forecast-driven policy are evaluated in a 28-day rolling one-step decision simulation.
- The live calculator is a single-item decision aid; its on-hand input is only a proxy for inventory position.
- Lead times are deterministic; supplier delays and fill-rate uncertainty are not modeled.
- The public dataset does not include actual stock-on-hand, open purchase orders, reservations, pack sizes, supplier constraints, or actual warehouse/store assignments.
- The normal safety-stock approximation can be inaccurate for intermittent, skewed or highly seasonal demand.
- Conformal residual calibration is empirical and can lose coverage under temporal dependence or distribution shift.
- Cost parameters are assumptions, not retailer-provided economics; simulated cost reduction is not realized savings.
- The forecast target is observed sales, which can differ from latent customer demand when stockouts occur.
