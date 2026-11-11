"""Lead-time, service-level and cost sensitivity for periodic-review inventory."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.inventory.inventory_policy import InventoryPolicy, calculate_policy
from src.simulation.inventory_simulator import simulate
from src.utils.config import ROOT, load_yaml


COST_SCENARIOS = {
    "low_stockout_penalty": {"holding": 1.0, "ordering": 1.0, "stockout": 0.5},
    "base": {"holding": 1.0, "ordering": 1.0, "stockout": 1.0},
    "high_stockout_penalty": {"holding": 1.0, "ordering": 1.0, "stockout": 2.5},
    "high_holding_cost": {"holding": 2.0, "ordering": 1.0, "stockout": 1.0},
    "high_ordering_cost": {"holding": 1.0, "ordering": 2.0, "stockout": 1.0},
}


def run_policy(period, policy, mean_demand, lead, costs, inv_cfg):
    return simulate(
        period[["date", "demand"]],
        policy,
        initial_inventory=max(mean_demand * lead, float(inv_cfg["min_order_quantity"])),
        lead_time_days=lead,
        holding_cost_per_unit_day=float(inv_cfg["holding_cost_per_unit_day"]) * costs["holding"],
        ordering_cost_per_order=float(inv_cfg["ordering_cost_per_order"]) * costs["ordering"],
        stockout_cost_per_unit=float(inv_cfg["stockout_cost_per_unit"]) * costs["stockout"],
        review_start_date=period.date.min(),
    )


def summarize(sim):
    demand = float(sim["demand"].sum())
    fulfilled = float(sim["fulfilled"].sum())
    return {
        "total_cost": float(sim["total_cost"].sum()),
        "holding_cost": float(sim["holding_cost"].sum()),
        "ordering_cost": float(sim["ordering_cost"].sum()),
        "stockout_cost": float(sim["stockout_cost"].sum()),
        "stockout_units": float(sim["stockout_units"].sum()),
        "average_inventory": float(sim["ending_inventory"].mean()),
        "fill_rate": fulfilled / demand if demand else 1.0,
        "fulfilled_units": fulfilled,
        "demand_units": demand,
    }


def main() -> None:
    model_cfg = load_yaml("model_config.yaml")
    inv_cfg = load_yaml("inventory_config.yaml")
    source = ROOT / "data/processed/forecast_features.parquet"
    if not source.exists():
        raise FileNotFoundError("Run build_features first.")
    df = pd.read_parquet(source)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["id", "date"])
    dates = pd.DatetimeIndex(sorted(df.date.unique()))
    test_start = dates[-int(model_cfg["test_days"])]
    validation_start = dates[-(int(model_cfg["test_days"]) + int(model_cfg["validation_days"]))]
    train = df[df.date < validation_start]
    test = df[df.date >= test_start]
    if train.empty or test.empty:
        raise RuntimeError("Insufficient chronological history for sensitivity analysis.")

    # Deterministic, demand-stratified sample bounds runtime while retaining variety.
    series_volume = train.groupby("id", observed=True)["demand"].sum().sort_values()
    if len(series_volume) > 30:
        positions = np.linspace(0, len(series_volume) - 1, 30).round().astype(int)
        selected_ids = series_volume.iloc[positions].index
    else:
        selected_ids = series_volume.index

    rows = []
    review_period = int(inv_cfg["default_review_period_days"])
    # A lead-time replenishment must be able to arrive inside the held-out
    # evaluation window; otherwise all service-level policies can look identical.
    max_evaluable_lead = int(inv_cfg["test_days"] if "test_days" in inv_cfg else model_cfg["test_days"]) - review_period
    lead_times = [lead for lead in [1, 3, 5, 7, 10, 14, 21, 30] if lead <= max_evaluable_lead]
    if not lead_times:
        raise RuntimeError("Test window is too short for the configured review period and lead-time grid.")
    service_levels = [0.80, 0.85, 0.90, 0.95, 0.97]
    for sid in selected_ids:
        history = train[train.id == sid].sort_values("date").tail(int(inv_cfg["demand_window_days"]))
        period = test[test.id == sid].sort_values("date")
        if history.empty or period.empty:
            continue
        mean_demand = max(0.0, float(history.demand.mean()))
        std_demand = float(history.demand.std(ddof=1)) if len(history) > 1 else 0.0
        std_demand = 0.0 if not np.isfinite(std_demand) else max(0.0, std_demand)

        for lead in lead_times:
            for cost_name, multipliers in COST_SCENARIOS.items():
                baseline = calculate_policy(InventoryPolicy(
                    mean_demand, std_demand, lead, 0.80, review_period,
                    float(inv_cfg["min_order_quantity"]), float(inv_cfg["max_order_quantity"]),
                ))
                baseline_metrics = summarize(run_policy(period, baseline, mean_demand, lead, multipliers, inv_cfg))
                for service_level in service_levels:
                    candidate = calculate_policy(InventoryPolicy(
                        mean_demand, std_demand, lead, service_level, review_period,
                        float(inv_cfg["min_order_quantity"]), float(inv_cfg["max_order_quantity"]),
                    ))
                    candidate_metrics = summarize(run_policy(period, candidate, mean_demand, lead, multipliers, inv_cfg))
                    rows.append({
                        "id": str(sid), "lead_time_days": lead,
                        "review_period_days": review_period,
                        "service_level_target": service_level,
                        "cost_scenario": cost_name,
                        "baseline_service_level_target": 0.80,
                        **{f"baseline_{k}": v for k, v in baseline_metrics.items()},
                        **{f"candidate_{k}": v for k, v in candidate_metrics.items()},
                    })

    if not rows:
        raise RuntimeError("No series available for sensitivity simulation.")
    result = pd.DataFrame(rows)
    result["cost_change_pct_vs_80pct"] = np.where(
        result["baseline_total_cost"] > 0,
        (result["candidate_total_cost"] - result["baseline_total_cost"]) / result["baseline_total_cost"] * 100,
        np.nan,
    )
    result["stockout_change_pct_vs_80pct"] = np.where(
        result["baseline_stockout_units"] > 0,
        (result["candidate_stockout_units"] - result["baseline_stockout_units"]) / result["baseline_stockout_units"] * 100,
        np.nan,
    )
    out = ROOT / "reports/tables"
    out.mkdir(parents=True, exist_ok=True)
    result.to_csv(out / "inventory_sensitivity_by_series.csv", index=False)
    summary = result.groupby(
        ["lead_time_days", "service_level_target", "cost_scenario"], as_index=False
    ).agg(
        baseline_total_cost=("baseline_total_cost", "sum"),
        candidate_total_cost=("candidate_total_cost", "sum"),
        baseline_stockout_units=("baseline_stockout_units", "sum"),
        candidate_stockout_units=("candidate_stockout_units", "sum"),
        baseline_fill_rate=("baseline_fill_rate", "mean"),
        candidate_fill_rate=("candidate_fill_rate", "mean"),
        baseline_average_inventory=("baseline_average_inventory", "mean"),
        candidate_average_inventory=("candidate_average_inventory", "mean"),
        baseline_fulfilled_units=("baseline_fulfilled_units", "sum"),
        candidate_fulfilled_units=("candidate_fulfilled_units", "sum"),
        baseline_demand_units=("baseline_demand_units", "sum"),
        candidate_demand_units=("candidate_demand_units", "sum"),
        series_count=("id", "nunique"),
    )
    summary["baseline_fill_rate"] = np.where(
        summary.baseline_demand_units > 0,
        summary.baseline_fulfilled_units / summary.baseline_demand_units,
        1.0,
    )
    summary["candidate_fill_rate"] = np.where(
        summary.candidate_demand_units > 0,
        summary.candidate_fulfilled_units / summary.candidate_demand_units,
        1.0,
    )
    summary["fill_rate_change_pp"] = (
        summary["candidate_fill_rate"] - summary["baseline_fill_rate"]
    ) * 100
    summary["cost_change_pct_vs_80pct"] = np.where(
        summary.baseline_total_cost > 0,
        (summary.candidate_total_cost - summary.baseline_total_cost) / summary.baseline_total_cost * 100,
        np.nan,
    )
    summary["stockout_change_pct_vs_80pct"] = np.where(
        summary.baseline_stockout_units > 0,
        (summary.candidate_stockout_units - summary.baseline_stockout_units) / summary.baseline_stockout_units * 100,
        np.nan,
    )
    summary.to_csv(out / "inventory_sensitivity_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
