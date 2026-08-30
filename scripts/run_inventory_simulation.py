"""Select and evaluate periodic-review inventory policies without test leakage."""

from __future__ import annotations

import pandas as pd

from src.inventory.inventory_policy import InventoryPolicy, calculate_policy
from src.simulation.inventory_simulator import simulate
from src.utils.config import ROOT, load_yaml


def split_data(df: pd.DataFrame, validation_days: int, test_days: int):
    """Create chronological train/validation/test periods."""
    max_date = pd.Timestamp(df["date"].max())
    test_start = max_date - pd.Timedelta(days=test_days - 1)
    validation_start = test_start - pd.Timedelta(days=validation_days)

    train = df[df["date"] < validation_start].copy()
    validation = df[
        (df["date"] >= validation_start)
        & (df["date"] < test_start)
    ].copy()
    test = df[df["date"] >= test_start].copy()

    return train, validation, test


def robust_demand_statistics(
    train_series: pd.DataFrame,
    window_days: int,
) -> tuple[float, float]:
    """Estimate mean and daily standard deviation from a configurable recent window."""
    if window_days < 1:
        raise ValueError("demand_window_days must be at least 1.")

    recent = train_series.sort_values("date").tail(window_days)["demand"]
    mean = max(0.0, float(recent.mean()))
    std = float(recent.std(ddof=1)) if len(recent) > 1 else 0.0

    if pd.isna(std):
        std = 0.0

    return mean, max(0.0, std)


def main() -> None:
    """Optimize periodic-review policies on validation and evaluate on test."""
    inventory_cfg = load_yaml("inventory_config.yaml")
    model_cfg = load_yaml("model_config.yaml")

    source = ROOT / "data/processed/forecast_features.parquet"
    if not source.exists():
        raise FileNotFoundError(
            "Missing prerequisite: data/processed/forecast_features.parquet. "
            "Run python -m scripts.build_features first."
        )

    df = pd.read_parquet(source)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["id", "date"])

    train, validation, test = split_data(
        df,
        int(model_cfg["validation_days"]),
        int(model_cfg["test_days"]),
    )

    demand_window = int(inventory_cfg["demand_window_days"])
    outputs: list[pd.DataFrame] = []
    policy_records: list[dict] = []

    for series_id, train_series in train.groupby("id", observed=True):
        validation_series = validation[validation["id"] == series_id].sort_values("date")
        test_series = test[test["id"] == series_id].sort_values("date")

        if validation_series.empty or test_series.empty:
            continue

        mean_daily_demand, demand_std = robust_demand_statistics(
            train_series,
            demand_window,
        )

        baseline_policy = calculate_policy(
            InventoryPolicy(
                mean_daily_demand=mean_daily_demand,
                demand_std=demand_std,
                lead_time_days=int(inventory_cfg["baseline_lead_time_days"]),
                service_level=float(inventory_cfg["baseline_service_level"]),
                review_period_days=int(inventory_cfg["baseline_review_period_days"]),
                min_order_quantity=float(inventory_cfg["min_order_quantity"]),
                max_order_quantity=float(inventory_cfg["max_order_quantity"]),
            )
        )

        def evaluate(period: pd.DataFrame, policy: dict) -> pd.DataFrame:
            return simulate(
                period[["date", "demand"]],
                policy,
                initial_inventory=max(
                    mean_daily_demand * policy["lead_time_days"],
                    float(inventory_cfg["min_order_quantity"]),
                ),
                lead_time_days=policy["lead_time_days"],
                holding_cost_per_unit_day=float(
                    inventory_cfg["holding_cost_per_unit_day"]
                ),
                ordering_cost_per_order=float(
                    inventory_cfg["ordering_cost_per_order"]
                ),
                stockout_cost_per_unit=float(
                    inventory_cfg["stockout_cost_per_unit"]
                ),
                review_start_date=period["date"].min(),
            )

        candidates: list[tuple[float, dict]] = []

        for service_level in inventory_cfg["service_levels"]:
            for review_period in inventory_cfg["review_periods"]:
                candidate = calculate_policy(
                    InventoryPolicy(
                        mean_daily_demand=mean_daily_demand,
                        demand_std=demand_std,
                        lead_time_days=int(inventory_cfg["default_lead_time_days"]),
                        service_level=float(service_level),
                        review_period_days=int(review_period),
                        min_order_quantity=float(inventory_cfg["min_order_quantity"]),
                        max_order_quantity=float(inventory_cfg["max_order_quantity"]),
                    )
                )
                validation_result = evaluate(validation_series, candidate)
                validation_cost = float(validation_result["total_cost"].sum())
                candidates.append((validation_cost, candidate))

        validation_cost, selected_policy = min(
            candidates,
            key=lambda pair: (
                pair[0],
                -pair[1]["service_level"],
                pair[1]["review_period_days"],
            ),
        )

        baseline_test = evaluate(test_series, baseline_policy).assign(
            policy="baseline",
            id=series_id,
        )
        optimized_test = evaluate(test_series, selected_policy).assign(
            policy="optimized",
            id=series_id,
        )

        outputs.extend([baseline_test, optimized_test])
        policy_records.append(
            {
                "id": series_id,
                "validation_total_cost": validation_cost,
                **selected_policy,
            }
        )

    if not outputs:
        raise RuntimeError(
            "No complete validation/test series were available for inventory simulation."
        )

    simulation_output = pd.concat(
        outputs,
        ignore_index=True,
    )

    simulation_path = ROOT / "data/processed/inventory_simulation.parquet"
    policy_path = ROOT / "data/processed/optimized_policies.parquet"

    simulation_output.to_parquet(
        simulation_path,
        index=False,
    )

    pd.DataFrame(policy_records).to_parquet(
        policy_path,
        index=False,
    )

    print(
        f"Simulated {len(policy_records)} series over the identical held-out test period."
    )
    print(
        f"Inventory demand window: {demand_window} days."
    )
    print(
        f"MOQ assumption: {inventory_cfg['min_order_quantity']} units."
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
