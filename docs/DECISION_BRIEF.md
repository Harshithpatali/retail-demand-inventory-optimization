# Decision Brief — Forecast-Driven Replenishment

## Executive decision

**Decision owner:** Retail inventory planner / replenishment manager  
**Decision:** In the evaluated 200-series M5 modelling panel, the forecast-driven replenishment policy is a promising candidate for a controlled pilot under the stated cost assumptions. It is not evidence of realized retailer savings.

## Evidence

On the final 28-day test period, mean per-series simulation metrics were:

| Metric | Historical-demand baseline | Forecast-driven policy | Change |
|---|---:|---:|---:|
| Simulated total cost | 299.76 | 246.95 | -17.62% |
| Stockout units | 53.92 | 43.10 | -20.05% |
| Average ending inventory | 122.95 | 90.12 | -26.70% |
| Fill rate | 93.88% | 94.21% | +0.32 pp |

The model's pooled rolling-origin WAPE was 29.11% versus 34.49% for a 7-day moving average, 38.62% for naive and 40.29% for seasonal naive across 22,400 observations.

## Decision caveats

- Results cover a selected 200-series panel, not all 30,490 item-store series.
- Inventory outcomes are simulation outputs under explicit holding, ordering and stockout cost assumptions.
- The evaluation uses a 28-day rolling one-step decision simulation.
- Supplier lead-time uncertainty, actual purchase orders, realized margins and store-specific operating constraints are not observed.

## Recommended next action

Run a shadow replenishment evaluation with a retailer's actual SKU-store data, lead-time distributions, service-level targets and finance-approved cost inputs. Compare the policy with current planner decisions before any live pilot.

## Stakeholder handoff

The inventory planner should confirm lead time, review cadence, target service level, minimum order quantities and capacity constraints. Finance should validate holding, ordering and stockout cost assumptions. Operations should define exception handling and override reasons. Record these assumptions alongside each simulation run.

## Collaboration and provenance

This is an independently developed portfolio project using public M5 competition data. The planner, finance and operations roles describe the intended decision workflow; they are **not claims of client engagement, retailer deployment or stakeholder sign-off**.

**Source of truth:** [Empirical evaluation results](empirical_evaluation_results.md) and [network geography policy](network_intelligence_data_policy.md).