# Inventory methodology

The project uses a periodic-review `(R,S)` inventory policy.

## Demand statistics

For each item-store series, inventory-policy demand statistics are estimated from the most recent configurable training window. The default is **365 days**, chosen to reduce sensitivity to a short recent window in a highly intermittent demand series.

## Periodic review

`R` is the review period. The simulator checks the inventory position only on scheduled review dates.

`S` is the target inventory position. At a review:

- inventory position = on-hand + outstanding purchase orders
- if inventory position is below `S`, place an order toward `S`
- the order arrives only after the configured lead time

## Protection period

For periodic review, the protected period is:

`L + R`

where `L` is lead time and `R` is review period.

The independent daily-demand approximation uses:

`Safety Stock = z * sigma_daily * sqrt(L + R)`

and:

`S = mean_daily_demand * (L + R) + Safety Stock`

The same uncertainty is not added again elsewhere in the inventory calculation.

## Replenishment constraints

Orders respect configurable minimum and maximum quantities. The default minimum order quantity is **5 units** and is a simulation assumption intended to avoid unrealistically frequent 1-unit purchase orders. It is not a claim about a real retailer's MOQ.

## Policy optimization

The project searches:

- 6 service levels
- 6 review periods

for 36 candidate policies per series. Candidates are evaluated on the validation period using total cost:

`Holding Cost + Ordering Cost + Stockout Cost`

The lowest-cost validation policy is selected and evaluated once on the held-out test period.
