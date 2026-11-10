# Network Intelligence: data and location policy

## Observed data
The M5 dataset provides store identifiers and state codes (for example, CA_1, TX_1, WI_1). It does not provide verified street addresses, store coordinates, warehouse coordinates, or a distribution-centre assignment.

## Map representation
- Store performance is aggregated at state level.
- State reference coordinates are approximate centroids and must never be shown as store pins.
- The state choropleth uses state codes from the M5 data.
- Do not infer a precise store address from a store identifier.

## Synthetic network layer
The distribution-centre records in `data/reference/simulated_distribution_centers.csv` are synthetic scenario anchors near representative cities. They are not real facilities and are not verified logistics locations.
- Stores are assigned to a synthetic centre by matching the M5 state code.
- The assignment is a scenario assumption, not an observed retailer relationship.
- The current demonstration does not calculate real road distances, route costs, or actual service territories.

## Future real-world enrichment
Only replace a state-level proxy with a real store or warehouse point when an authoritative source provides a verified address or coordinate and a defensible match to the M5 store. Keep provenance, match confidence, and observation date with every enriched record.
