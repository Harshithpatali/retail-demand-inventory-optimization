# Business and inventory assumptions

## Interpretation

Holding, ordering and stockout costs in this repository are **simulation assumptions**, not actual retailer financial data. The project does not claim realized savings, revenue lift, margin improvement or retailer deployment. Reported business impact is a comparison of simulated policies under a declared configuration.

## Configured economic parameters

The source of truth is `configs/inventory_config.yaml`.

| Parameter | Value | How the simulator uses it |
|---|---:|---|
| Holding cost | 0.05 per unit-day | Applied to inventory carried each simulated day |
| Ordering cost | 5.00 per order | Fixed charge when an order is placed |
| Stockout cost | 2.00 per unmet unit | Penalty proxy for unmet demand |
| Baseline service level | 80% | Historical-demand comparator target |
| Default service level | 90% | Default planning target |
| Baseline lead time | 7 days | Deterministic delay between order and receipt |
| Default lead time | 7 days | Default planning delay |
| Baseline/default review period | 7 days | Days between periodic inventory reviews |
| Minimum order quantity | 5 units | Configured simulation minimum |
| Maximum order quantity | 500 units | Configured simulation cap |
| Demand history window | 365 days | Recent history used by the live normal-approximation policy |

The public M5 dataset does not supply the retailer's true carrying cost, order processing cost, stockout economics, unit margin or currency denomination. Cost parameters are therefore abstract model units. Do not label the simulated totals as dollars, rupees or another currency.

## Replenishment assumptions

- **Protection period:** lead time plus review period.
- **Historical policy:** calculates expected demand from recent historical mean and estimates safety stock using a normal-demand approximation and target service-level z-score.
- **Forecast policy:** sums forecast demand over the protection period and adds an empirical block-conformal residual quantile as safety stock.
- **Policy selection:** candidate service levels and review periods are evaluated on a validation selection window. The chosen policy is frozen before the held-out test period.
- **Order limits:** MOQ and maximum order quantity are configurable; the live demo order suggestion is capped at 500 units.
- **Inventory position:** the live UI uses on-hand quantity as a proxy for inventory position because open purchase orders and reserved stock are not supplied.
- **Lead time:** simulation lead time is deterministic. The sensitivity experiment varies lead-time values but does not sample stochastic supplier delays.

## Simulation cost logic

The simulation uses three economic components:
1. Holding cost proportional to units held and days held.
2. Fixed ordering cost for each replenishment order.
3. Stockout penalty proportional to unmet demand units.

The resulting total cost is a synthetic objective for comparing policies under identical historical demand. It is not a complete retailer profit-and-loss calculation: there is no verified product margin, markdown, spoilage, shrinkage, transport cost, supplier discount or working-capital rate.

## What the data does not contain

M5 does not provide true latent demand, actual inventory positions, open purchase orders, reservations, supplier fill rates, supplier lead-time distributions, verified warehouse/store assignments, or finance-approved cost parameters. A real pilot would require those inputs, agreement from inventory/operations and finance stakeholders, and prospective shadow evaluation before live replenishment decisions.

## Full-population forecast assumptions

- The full-population model predicts observed M5 sales, not unconstrained customer demand.
- The source calendar does not provide future event/SNAP values beyond its historical horizon; unavailable future values are set to neutral values in the 28-day batch forecast.
- Future selling prices are not forecast by the model.
- The full-population 28-day forecast is a demand estimate, not an order recommendation. A replenishment decision additionally requires current stock, open orders, reservations, supplier lead-time distributions, review cadence, pack sizes/MOQs, and retailer-specific costs.
