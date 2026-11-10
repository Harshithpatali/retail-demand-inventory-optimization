"""Compare historical and forecast-driven inventory policies on held-out demand.

Validation is split chronologically: the first half calibrates residual
uncertainty; the second half selects the inventory policy. The selected target
is frozen before the held-out test period. Forecast rows use one-step-ahead
features, so each prediction assumes prior-day demand is observable.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from src.features.feature_pipeline import MODEL_FEATURES
from src.inventory.forecast_policy import calculate_forecast_target
from src.inventory.inventory_policy import InventoryPolicy, calculate_policy
from src.simulation.inventory_simulator import simulate
from src.simulation.simulator_metrics import summarize_simulation
from src.utils.config import ROOT, load_yaml


def run_simulation(period, policy, mean_daily, inv_cfg, lead_time):
    return simulate(
        period[["date", "demand"]], policy,
        initial_inventory=max(mean_daily * lead_time, float(inv_cfg["min_order_quantity"])),
        lead_time_days=lead_time,
        holding_cost_per_unit_day=float(inv_cfg["holding_cost_per_unit_day"]),
        ordering_cost_per_order=float(inv_cfg["ordering_cost_per_order"]),
        stockout_cost_per_unit=float(inv_cfg["stockout_cost_per_unit"]),
        review_start_date=period.date.min(),
    )


def main():
    model_cfg = load_yaml("model_config.yaml")
    inv_cfg = load_yaml("inventory_config.yaml")
    data_path = ROOT / "data/processed/forecast_features.parquet"
    model_path = ROOT / "models/forecasting/validation_model.joblib"
    if not data_path.exists() or not model_path.exists():
        raise FileNotFoundError("Run build_features and train_models first.")

    frame = pd.read_parquet(data_path).sort_values(["id", "date"])
    max_date = pd.to_datetime(frame.date).max()
    test_start = max_date - pd.Timedelta(days=int(model_cfg["test_days"]) - 1)
    val_start = test_start - pd.Timedelta(days=int(model_cfg["validation_days"]))
    train = frame[frame.date < val_start]
    val = frame[(frame.date >= val_start) & (frame.date < test_start)].copy()
    test = frame[frame.date >= test_start].copy()
    bundle = joblib.load(model_path)
    val["prediction"] = np.maximum(0.0, bundle["model"].predict(val[MODEL_FEATURES]))
    test["prediction"] = np.maximum(0.0, bundle["model"].predict(test[MODEL_FEATURES]))
    val["residual"] = val.demand.to_numpy() - val.prediction.to_numpy()

    rows, policy_rows = [], []
    for sid, test_group in test.groupby("id", observed=True):
        vg = val[val.id == sid].sort_values("date")
        tg = test_group.sort_values("date")
        if len(vg) < 20 or tg.empty:
            continue

        # Chronological split prevents reusing calibration errors for policy selection.
        midpoint = len(vg) // 2
        calibration = vg.iloc[:midpoint]
        selection = vg.iloc[midpoint:]
        residuals = calibration.residual.to_numpy()
        selection_forecast = selection.prediction.to_numpy()
        lead = int(inv_cfg["default_lead_time_days"])
        feasible_reviews = [int(rp) for rp in inv_cfg["review_periods"]
                            if lead + int(rp) <= len(selection)]
        if not feasible_reviews:
            continue

        hist = train[train.id == sid].sort_values("date").tail(
            int(inv_cfg["demand_window_days"])
        ).demand
        hist_mean = max(0.0, float(hist.mean()))
        hist_std = float(hist.std(ddof=1)) if len(hist) > 1 else 0.0
        baseline = calculate_policy(InventoryPolicy(
            hist_mean, max(0.0, hist_std), lead,
            float(inv_cfg["baseline_service_level"]),
            int(inv_cfg["baseline_review_period_days"]),
            float(inv_cfg["min_order_quantity"]), float(inv_cfg["max_order_quantity"])
        ))

        candidates = []
        for sl in inv_cfg["service_levels"]:
            for rp in feasible_reviews:
                candidate = calculate_forecast_target(
                    selection_forecast, residuals, lead, rp, float(sl),
                    float(inv_cfg["min_order_quantity"]), float(inv_cfg["max_order_quantity"])
                )
                selection_sim = run_simulation(selection, candidate, hist_mean, inv_cfg, lead)
                candidates.append((float(selection_sim.total_cost.sum()), candidate))
        _, selected = min(candidates, key=lambda pair: (
            pair[0], -pair[1]["service_level"], pair[1]["review_period_days"]
        ))

        # Freeze the validation-selected policy; test demand is used only for scoring.
        baseline_test = run_simulation(tg, baseline, hist_mean, inv_cfg, lead)
        optimized_test = run_simulation(tg, selected, hist_mean, inv_cfg, lead)
        rows.extend([
            {"id": str(sid), "policy": "historical_baseline", **summarize_simulation(baseline_test)},
            {"id": str(sid), "policy": "forecast_driven", **summarize_simulation(optimized_test)},
        ])
        policy_rows.append({"id": str(sid), **selected})

    if not rows:
        raise RuntimeError("No series had sufficient calibration, selection, and test observations.")
    output_dir = ROOT / "reports/tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "forecast_driven_inventory_comparison.csv", index=False)
    result.groupby("policy").mean(numeric_only=True).to_csv(
        output_dir / "forecast_driven_inventory_summary.csv"
    )
    pd.DataFrame(policy_rows).to_csv(
        output_dir / "forecast_driven_selected_policies.csv", index=False
    )
    print(result.groupby("policy")[[
        "total_cost", "stockout_units", "average_inventory", "fill_rate"
    ]].mean())


if __name__ == "__main__":
    main()
