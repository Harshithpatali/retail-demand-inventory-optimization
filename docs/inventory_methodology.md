# Inventory methodology

## Live API and dashboard policy

The interactive inventory endpoint and dashboard use the same periodic-review `(R,S)` calculation implemented in `src/inventory/inventory_policy.py`.

- Demand statistics use the most recent **365 observations** by default (configurable with `API_HISTORY_DAYS`, bounded to 56–1,825 days).
- Review period defaults to **7 days**.
- Protection period is **lead time + review period**.
- Target inventory position is expected protection-period demand plus safety stock.
- Suggested order quantity is the positive gap between target inventory position and the entered on-hand quantity, capped at 500 units.
- The live interface treats on-hand stock as inventory position because the dataset and UI do not provide open purchase orders or reservations. This is an explicit simplifying assumption, not a complete ERP inventory-position calculation.

The live API and dashboard expose protection-period length, target inventory position and demand-history window so users can inspect the assumptions.

## Demand statistics and safety stock

Mean and sample standard deviation are calculated from the recent history window. Safety stock uses a normal-demand approximation:

`Safety Stock = z(service level) × sigma_daily × sqrt(L + R)`

and:

`Target S = mean_daily_demand × (L + R) + Safety Stock`

The normal approximation is a planning baseline. It can be inaccurate for intermittent, skewed or highly seasonal demand. The offline evaluation includes conformal residual diagnostics and Croston SBA as additional statistical checks.

## Replenishment constraints

Orders are capped at 500 units in the live demo. The cap is a protective demo assumption, not a retailer contract or MOQ. The offline simulator has its own configurable MOQ and maximum order constraints.

## Evaluation

The offline forecast-driven inventory experiment selects policy parameters on validation data and evaluates the frozen policy on held-out demand. Its simulated economics are separate from the interactive single-SKU calculator. They are not realized retailer savings.
