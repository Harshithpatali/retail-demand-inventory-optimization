"""Compare historical and forecast-driven inventory policies on a held-out period.

Forecast rows use the global model's one-step-ahead predictions with lag features
available at each date. This is a rolling operational interpretation: prior-day
actual demand is observable before the next day's order review. Policies are
selected using validation forecasts/residuals only; test demand is used solely
inside the simulator for scoring.
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
    val = frame[(frame.date >= val_start) & (frame.date < test_start)]
    test = frame[frame.date >= test_start]
    bundle = joblib.load(model_path)
    val = val.copy()
    test = test.copy()
    val["prediction"] = np.maximum(0.0, bundle["model"].predict(val[MODEL_FEATURES]))
    test["prediction"] = np.maximum(0.0, bundle["model"].predict(test[MODEL_FEATURES]))
    val["residual"] = val.demand.to_numpy() - val.prediction.to_numpy()

    rows = []
    policy_rows = []
    for sid, test_group in test.groupby("id", observed=True):
        vg = val[val.id == sid].sort_values("date")
        tg = test_group.sort_values("date")
        if vg.empty or tg.empty:
            continue
        residuals = vg.residual.to_numpy()
        forecast = tg.prediction.to_numpy()
        lead = int(inv_cfg["default_lead_time_days"])
        max_review = max(map(int, inv_cfg["review_periods"]))
        max_protection = lead + max_review
        if len(forecast) < max_protection:
            continue

        hist = train[train.id == sid].sort_values("date").tail(int(inv_cfg["demand_window_days"])).demand
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
            for rp in inv_cfg["review_periods"]:
                candidate = calculate_forecast_target(
                    forecast, residuals, lead, int(rp), float(sl),
                    float(inv_cfg["min_order_quantity"]), float(inv_cfg["max_order_quantity"])
                )
                # Select on validation only: use validation residual blocks and
                # the first protection-period validation forecast.
                val_forecast = vg.prediction.to_numpy()
                if len(val_forecast) < lead + int(rp):
                    continue
                candidate_val = calculate_forecast_target(
                    val_forecast, residuals, lead, int(rp), float(sl),
                    float(inv_cfg["min_order_quantity"]), float(inv_cfg["max_order_quantity"])
                )
                val_sim = simulate(
                    vg[["date", "demand"]], candidate_val,
                    initial_inventory=max(hist_mean * lead, float(inv_cfg["min_order_quantity"])),
                    lead_time_days=lead,
                    holding_cost_per_unit_day=float(inv_cfg["holding_cost_per_unit_day"]),
                    ordering_cost_per_order=float(inv_cfg["ordering_cost_per_order"]),
                    stockout_cost_per_unit=float(inv_cfg["stockout_cost_per_unit"]),
                    review_start_date=vg.date.min()
                )
                candidates.append((float(val_sim.total_cost.sum()), candidate_val))
        if not candidates:
            continue
        _, selected = min(candidates, key=lambda x: x[0])
        # Rebuild the selected policy target from the test-period forecast,
        # retaining only the service/review settings selected on validation.
        selected = calculate_forecast_target(
            forecast, residuals, lead, selected["review_period_days"],
            selected["service_level"], float(inv_cfg["min_order_quantity"]),
            float(inv_cfg["max_order_quantity"])
        )

        def run(policy):
            return simulate(
                tg[["date", "demand"]], policy,
                initial_inventory=max(hist_mean * lead, float(inv_cfg["min_order_quantity"])),
                lead_time_days=lead,
                holding_cost_per_unit_day=float(inv_cfg["holding_cost_per_unit_day"]),
                ordering_cost_per_order=float(inv_cfg["ordering_cost_per_order"]),
                stockout_cost_per_unit=float(inv_cfg["stockout_cost_per_unit"]),
                review_start_date=tg.date.min()
            )
        base_result = run(baseline)
        opt_result = run(selected)
        rows.extend([
            {"id": str(sid), "policy": "historical_baseline", **summarize_simulation(base_result)},
            {"id": str(sid), "policy": "forecast_driven", **summarize_simulation(opt_result)}
        ])
        policy_rows.append({"id": str(sid), **selected})

    if not rows:
        raise RuntimeError("No series had enough forecast horizon for the requested protection periods.")
    output_dir = ROOT / "reports/tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "forecast_driven_inventory_comparison.csv", index=False)
    result.groupby("policy").mean(numeric_only=True).to_csv(
        output_dir / "forecast_driven_inventory_summary.csv"
    )
    pd.DataFrame(policy_rows).to_csv(output_dir / "forecast_driven_selected_policies.csv", index=False)
    print(result.groupby("policy")[["total_cost", "stockout_units", "average_inventory", "fill_rate"]].mean())


if __name__ == "__main__":
    main()
