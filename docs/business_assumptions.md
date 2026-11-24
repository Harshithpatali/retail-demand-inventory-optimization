# Business assumptions

Holding, ordering and stockout costs are simulation assumptions. They are not actual retailer financial data. The project does not claim real-world savings. Business impact means simulated cost impact under the configured assumptions.


## Full-population forecast assumptions and limitations

- M5 sales are used as a proxy target; latent demand and lost sales are not observed.
- The M5 calendar does not provide future event/SNAP values beyond the historical period used for training; unavailable future covariates are set to neutral values.
- Future selling prices are not projected by this model.
- Forecasts cover 30,490 item-store series for 28 dates only when the generated Parquet passes row-count and unique-series verification.
- Any inventory policy comparison remains a simulation under declared holding, ordering, shortage-penalty, lead-time and review-period assumptions. It is not actual retailer savings.
- The data does not include real inventory positions, open purchase orders, reservations, supplier fill rates, stochastic lead times or verified retailer cost parameters. A real deployment requires those inputs and a prospective pilot.
