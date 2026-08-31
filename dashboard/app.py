
from __future__ import annotations

import os
from typing import Any

import httpx
import pandas as pd
import streamlit as st


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
).rstrip("/")


st.set_page_config(
    page_title="Retail Demand & Inventory",
    page_icon="📦",
    layout="wide",
)


# -------------------------------------------------------------------
# PAGE TITLE
# -------------------------------------------------------------------

st.title("Retail Demand Forecasting & Inventory Optimization")
st.caption(
    "Forecast demand, evaluate inventory policies, and explore business impact."
)


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def api_error_message() -> None:
    """Display a consistent API-unavailable message."""

    st.error(
        "API unavailable. Start FastAPI with:\n\n"
        "uvicorn api.main:app --reload"
    )


def get_json(
    endpoint: str,
    timeout: float = 10.0,
) -> dict[str, Any] | None:
    """Perform a GET request and return parsed JSON."""

    try:
        response = httpx.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as exc:
        st.error(
            f"API request failed: {exc}"
        )
        return None

    except ValueError:
        st.error(
            "API returned an invalid JSON response."
        )
        return None


def post_json(
    endpoint: str,
    payload: dict[str, Any],
    timeout: float = 30.0,
) -> dict[str, Any] | None:
    """Perform a POST request with a JSON body."""

    try:
        response = httpx.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get(
                "detail",
                str(exc),
            )
        except Exception:
            detail = str(exc)

        st.error(
            f"API request failed: {detail}"
        )
        return None

    except httpx.HTTPError as exc:
        st.error(
            f"API request failed: {exc}"
        )
        return None

    except ValueError:
        st.error(
            "API returned an invalid JSON response."
        )
        return None


def format_number(
    value: Any,
    decimals: int = 2,
) -> str:
    """Format numeric values for dashboard display."""

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def format_percent(
    value: Any,
    decimals: int = 2,
) -> str:
    """Format a fraction such as 0.9442 as 94.42%."""

    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def display_action(
    action: str,
) -> None:
    """Display inventory recommendation prominently."""

    normalized = str(action).upper()

    if normalized == "REORDER":
        st.error(
            "🔴 REORDER"
        )

    elif normalized == "HOLD":
        st.success(
            "🟢 HOLD"
        )

    else:
        st.warning(
            f"Recommendation: {normalized}"
        )


def business_metrics_to_dataframe(
    payload: dict[str, Any],
) -> pd.DataFrame:
    """Convert the API business summary into a metric comparison table.

    Expected API shape:

        {
            "available": true,
            "metrics": {
                "baseline": {
                    "total_cost": ...,
                    "holding_cost": ...,
                    ...
                },
                "optimized": {
                    "total_cost": ...,
                    "holding_cost": ...,
                    ...
                }
            }
        }

    Returns a table with:

        metric | baseline | optimized | change_pct
    """

    metrics = payload.get(
        "metrics",
        {},
    )

    if not isinstance(metrics, dict):
        return pd.DataFrame()

    baseline = metrics.get(
        "baseline",
        {},
    )

    optimized = metrics.get(
        "optimized",
        {},
    )

    if not isinstance(baseline, dict):
        baseline = {}

    if not isinstance(optimized, dict):
        optimized = {}

    metric_names = sorted(
        set(baseline.keys())
        | set(optimized.keys())
    )

    rows: list[dict[str, Any]] = []

    for metric_name in metric_names:

        baseline_value = baseline.get(
            metric_name
        )

        optimized_value = optimized.get(
            metric_name
        )

        try:
            baseline_numeric = float(
                baseline_value
            )
        except (TypeError, ValueError):
            baseline_numeric = None

        try:
            optimized_numeric = float(
                optimized_value
            )
        except (TypeError, ValueError):
            optimized_numeric = None

        if (
            baseline_numeric is not None
            and optimized_numeric is not None
            and baseline_numeric != 0
        ):
            change_pct = (
                (
                    optimized_numeric
                    - baseline_numeric
                )
                / baseline_numeric
                * 100
            )
        else:
            change_pct = None

        rows.append(
            {
                "metric": metric_name,
                "baseline": baseline_numeric,
                "optimized": optimized_numeric,
                "change_pct": change_pct,
            }
        )

    return pd.DataFrame(
        rows
    )


def metric_value(
    df: pd.DataFrame,
    metric_name: str,
    column: str,
) -> float | None:
    """Safely retrieve one business metric."""

    if df.empty:
        return None

    if "metric" not in df.columns:
        return None

    matches = df[
        df["metric"].astype(str)
        == metric_name
    ]

    if matches.empty:
        return None

    if column not in matches.columns:
        return None

    try:
        return float(
            matches.iloc[0][column]
        )
    except (TypeError, ValueError):
        return None


# -------------------------------------------------------------------
# LOAD AVAILABLE STORE / ITEM OPTIONS
# -------------------------------------------------------------------

options_payload = get_json(
    "/options",
    timeout=10,
)

if options_payload is None:
    api_error_message()
    st.stop()


options = options_payload.get(
    "options",
    [],
)

if not options:
    st.warning(
        "No store/item options available. "
        "Run the data and feature pipeline first."
    )
    st.stop()


pairs = pd.DataFrame(
    options
)

required_option_columns = {
    "store_id",
    "item_id",
}

if not required_option_columns.issubset(
    pairs.columns
):
    st.error(
        "The /options endpoint did not return "
        "store_id and item_id."
    )
    st.stop()


pairs["store_id"] = (
    pairs["store_id"]
    .astype(str)
)

pairs["item_id"] = (
    pairs["item_id"]
    .astype(str)
)


# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------

st.sidebar.header(
    "Controls"
)

stores = sorted(
    pairs["store_id"]
    .unique()
)

store = st.sidebar.selectbox(
    "Store ID",
    stores,
)


items = sorted(
    pairs.loc[
        pairs["store_id"] == store,
        "item_id",
    ]
    .astype(str)
    .unique()
)

item = st.sidebar.selectbox(
    "Item ID",
    items,
)


page = st.sidebar.radio(
    "Page",
    [
        "Executive Overview",
        "Demand Forecast",
        "Inventory Recommendation",
        "Business Impact",
        "Scenario Analysis",
    ],
)


service_level = st.sidebar.slider(
    "Service level",
    min_value=0.80,
    max_value=0.99,
    value=0.90,
    step=0.01,
)


lead_time = st.sidebar.slider(
    "Lead time (days)",
    min_value=1,
    max_value=30,
    value=7,
    step=1,
)


st.sidebar.divider()

st.sidebar.caption(
    f"API: {API_BASE_URL}"
)

st.sidebar.caption(
    f"Store: {store}"
)

st.sidebar.caption(
    f"Item: {item}"
)


# -------------------------------------------------------------------
# EXECUTIVE OVERVIEW
# -------------------------------------------------------------------

if page == "Executive Overview":

    st.header(
        "Executive Overview"
    )

    st.write(
        "Portfolio-level summary of the forecasting and inventory results."
    )

    payload = get_json(
        "/business",
        timeout=10,
    )

    if payload is None:
        api_error_message()
        st.stop()

    if not payload.get(
        "available",
        False,
    ):
        st.info(
            payload.get(
                "notes",
                "Business-impact artifacts are unavailable.",
            )
        )
        st.stop()

    metrics_df = business_metrics_to_dataframe(
        payload
    )

    if metrics_df.empty:
        st.warning(
            "Business metrics are available, "
            "but no structured metrics were returned."
        )
        st.stop()

    # Key KPI values.
    total_cost_baseline = metric_value(
        metrics_df,
        "total_cost",
        "baseline",
    )

    total_cost_optimized = metric_value(
        metrics_df,
        "total_cost",
        "optimized",
    )

    service_baseline = metric_value(
        metrics_df,
        "service_level",
        "baseline",
    )

    service_optimized = metric_value(
        metrics_df,
        "service_level",
        "optimized",
    )

    inventory_baseline = metric_value(
        metrics_df,
        "average_inventory",
        "baseline",
    )

    inventory_optimized = metric_value(
        metrics_df,
        "average_inventory",
        "optimized",
    )

    # KPI cards.
    col1, col2, col3, col4 = st.columns(
        4
    )

    with col1:
        st.metric(
            "Baseline Total Cost",
            format_number(
                total_cost_baseline
            ),
        )

    with col2:
        st.metric(
            "Optimized Total Cost",
            format_number(
                total_cost_optimized
            ),
            (
                f"{((total_cost_optimized - total_cost_baseline) / total_cost_baseline) * 100:+.2f}%"
                if total_cost_baseline not in (None, 0)
                and total_cost_optimized is not None
                else None
            ),
        )

    with col3:
        st.metric(
            "Optimized Service Level",
            format_percent(
                service_optimized
            ),
        )

    with col4:
        st.metric(
            "Optimized Avg Inventory",
            format_number(
                inventory_optimized
            ),
        )

    st.divider()

    # Cost comparison.
    cost_metrics = [
        "total_cost",
        "holding_cost",
        "ordering_cost",
        "stockout_cost",
    ]

    cost_rows = metrics_df[
        metrics_df["metric"].isin(
            cost_metrics
        )
    ].copy()

    if not cost_rows.empty:

        chart_df = cost_rows[
            [
                "metric",
                "baseline",
                "optimized",
            ]
        ].copy()

        chart_df = chart_df.set_index(
            "metric"
        )

        st.subheader(
            "Cost Comparison"
        )

        st.bar_chart(
            chart_df
        )

    # Full metrics table.
    st.subheader(
        "Business Metrics"
    )

    st.dataframe(
        metrics_df,
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# DEMAND FORECAST
# -------------------------------------------------------------------

elif page == "Demand Forecast":

    st.header(
        "Demand Forecast"
    )

    horizon = st.slider(
        "Forecast horizon",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
    )

    payload = post_json(
        "/forecast",
        {
            "store_id": store,
            "item_id": item,
            "horizon_days": horizon,
        },
        timeout=30,
    )

    if payload is None:
        api_error_message()
        st.stop()

    forecasts = payload.get(
        "forecasts",
        [],
    )

    if not forecasts:
        st.warning(
            "No forecasts were returned."
        )
        st.stop()

    forecast_df = pd.DataFrame(
        forecasts
    )

    if "date" not in forecast_df.columns:
        st.error(
            "Forecast response does not contain dates."
        )
        st.stop()

    forecast_df["date"] = pd.to_datetime(
        forecast_df["date"]
    )

    forecast_df = forecast_df.sort_values(
        "date"
    )

    st.subheader(
        f"{store} × {item}"
    )

    model_col, uncertainty_col = st.columns(
        2
    )

    with model_col:
        st.metric(
            "Forecast Model",
            payload.get(
                "model_name",
                "Unknown",
            ),
        )

    with uncertainty_col:
        st.metric(
            "Residual Std",
            format_number(
                payload.get(
                    "residual_std"
                ),
                3,
            ),
        )

    st.subheader(
        "Forecast with Prediction Interval"
    )

    chart_columns = [
        column
        for column in [
            "forecast",
            "lower",
            "upper",
        ]
        if column in forecast_df.columns
    ]

    if chart_columns:
        st.line_chart(
            forecast_df.set_index(
                "date"
            )[chart_columns]
        )

    st.subheader(
        "Forecast Table"
    )

    display_forecast = forecast_df.copy()

    for column in [
        "forecast",
        "lower",
        "upper",
    ]:
        if column in display_forecast.columns:
            display_forecast[column] = (
                display_forecast[column]
                .astype(float)
                .round(2)
            )

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# INVENTORY RECOMMENDATION
# -------------------------------------------------------------------

elif page == "Inventory Recommendation":

    st.header(
        "Inventory Recommendation"
    )

    current_inventory = st.number_input(
        "Current inventory",
        min_value=0.0,
        value=20.0,
        step=1.0,
    )

    payload = post_json(
        "/inventory",
        {
            "store_id": store,
            "item_id": item,
            "service_level": service_level,
            "lead_time_days": lead_time,
            "current_inventory": current_inventory,
        },
        timeout=30,
    )

    if payload is None:
        api_error_message()
        st.stop()

    st.subheader(
        f"{store} × {item}"
    )

    st.write(
        "Recommended inventory policy based on "
        "the selected service level and lead time."
    )

    # Recommendation banner.
    action_col, service_col, lead_col = st.columns(
        3
    )

    with action_col:
        st.write(
            "**Recommended Action**"
        )
        display_action(
            payload.get(
                "recommended_action",
                "UNKNOWN",
            )
        )

    with service_col:
        st.metric(
            "Service Level",
            format_percent(
                payload.get(
                    "service_level"
                )
            ),
        )

    with lead_col:
        st.metric(
            "Lead Time",
            f"{payload.get('lead_time_days', lead_time)} days",
        )

    st.divider()

    # Main inventory metrics.
    col1, col2, col3, col4 = st.columns(
        4
    )

    with col1:
        st.metric(
            "Mean Daily Demand",
            format_number(
                payload.get(
                    "mean_daily_demand"
                )
            ),
        )

    with col2:
        st.metric(
            "Lead-Time Demand",
            format_number(
                payload.get(
                    "lead_time_demand"
                )
            ),
        )

    with col3:
        st.metric(
            "Safety Stock",
            format_number(
                payload.get(
                    "safety_stock"
                )
            ),
        )

    with col4:
        st.metric(
            "Reorder Point",
            format_number(
                payload.get(
                    "reorder_point"
                )
            ),
        )

    col5, col6, col7 = st.columns(
        3
    )

    with col5:
        st.metric(
            "Order Quantity",
            format_number(
                payload.get(
                    "order_quantity"
                )
            ),
        )

    with col6:
        st.metric(
            "Current Inventory",
            format_number(
                payload.get(
                    "current_inventory"
                )
            ),
        )

    with col7:
        st.metric(
            "Demand Std",
            format_number(
                payload.get(
                    "demand_std"
                ),
                3,
            ),
        )

    st.divider()

    # Inventory policy table.
    inventory_rows = pd.DataFrame(
        [
            {
                "Metric": "Mean daily demand",
                "Value": payload.get(
                    "mean_daily_demand"
                ),
            },
            {
                "Metric": "Lead-time demand",
                "Value": payload.get(
                    "lead_time_demand"
                ),
            },
            {
                "Metric": "Demand standard deviation",
                "Value": payload.get(
                    "demand_std"
                ),
            },
            {
                "Metric": "Safety stock",
                "Value": payload.get(
                    "safety_stock"
                ),
            },
            {
                "Metric": "Reorder point",
                "Value": payload.get(
                    "reorder_point"
                ),
            },
            {
                "Metric": "Order quantity",
                "Value": payload.get(
                    "order_quantity"
                ),
            },
        ]
    )

    inventory_rows["Value"] = (
        inventory_rows["Value"]
        .astype(float)
        .round(3)
    )

    st.subheader(
        "Inventory Policy Details"
    )

    st.dataframe(
        inventory_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Model: {payload.get('model_name', 'Unknown')}"
    )


# -------------------------------------------------------------------
# BUSINESS IMPACT
# -------------------------------------------------------------------

elif page == "Business Impact":

    st.header(
        "Business Impact"
    )

    payload = get_json(
        "/business",
        timeout=10,
    )

    if payload is None:
        api_error_message()
        st.stop()

    if not payload.get(
        "available",
        False,
    ):
        st.info(
            payload.get(
                "notes",
                "Business-impact artifacts are unavailable.",
            )
        )
        st.stop()

    metrics_df = business_metrics_to_dataframe(
        payload
    )

    if metrics_df.empty:
        st.warning(
            "No business metrics were returned."
        )
        st.stop()

    # Key metrics.
    total_cost_baseline = metric_value(
        metrics_df,
        "total_cost",
        "baseline",
    )

    total_cost_optimized = metric_value(
        metrics_df,
        "total_cost",
        "optimized",
    )

    holding_baseline = metric_value(
        metrics_df,
        "holding_cost",
        "baseline",
    )

    holding_optimized = metric_value(
        metrics_df,
        "holding_cost",
        "optimized",
    )

    stockout_baseline = metric_value(
        metrics_df,
        "stockout_cost",
        "baseline",
    )

    stockout_optimized = metric_value(
        metrics_df,
        "stockout_cost",
        "optimized",
    )

    service_baseline = metric_value(
        metrics_df,
        "service_level",
        "baseline",
    )

    service_optimized = metric_value(
        metrics_df,
        "service_level",
        "optimized",
    )

    # KPI cards.
    c1, c2, c3, c4 = st.columns(
        4
    )

    with c1:
        st.metric(
            "Total Cost",
            format_number(
                total_cost_optimized
            ),
            (
                f"{((total_cost_optimized - total_cost_baseline) / total_cost_baseline) * 100:+.2f}%"
                if total_cost_baseline not in (None, 0)
                and total_cost_optimized is not None
                else None
            ),
        )

    with c2:
        st.metric(
            "Holding Cost",
            format_number(
                holding_optimized
            ),
            (
                f"{((holding_optimized - holding_baseline) / holding_baseline) * 100:+.2f}%"
                if holding_baseline not in (None, 0)
                and holding_optimized is not None
                else None
            ),
        )

    with c3:
        st.metric(
            "Stockout Cost",
            format_number(
                stockout_optimized
            ),
            (
                f"{((stockout_optimized - stockout_baseline) / stockout_baseline) * 100:+.2f}%"
                if stockout_baseline not in (None, 0)
                and stockout_optimized is not None
                else None
            ),
        )

    with c4:
        st.metric(
            "Service Level",
            format_percent(
                service_optimized
            ),
            (
                f"{(service_optimized - service_baseline) * 100:+.2f} pp"
                if service_baseline is not None
                and service_optimized is not None
                else None
            ),
        )

    st.divider()

    # Total cost chart.
    cost_names = [
        "total_cost",
        "holding_cost",
        "ordering_cost",
        "stockout_cost",
    ]

    cost_df = metrics_df[
        metrics_df["metric"].isin(
            cost_names
        )
    ].copy()

    if not cost_df.empty:

        st.subheader(
            "Cost Comparison"
        )

        cost_chart = cost_df[
            [
                "metric",
                "baseline",
                "optimized",
            ]
        ].copy()

        cost_chart = cost_chart.set_index(
            "metric"
        )

        st.bar_chart(
            cost_chart
        )

    # Inventory metrics.
    inventory_names = [
        "average_inventory",
        "max_inventory",
        "stockout_units",
        "stockout_days",
        "orders",
    ]

    inventory_df = metrics_df[
        metrics_df["metric"].isin(
            inventory_names
        )
    ].copy()

    if not inventory_df.empty:

        st.subheader(
            "Inventory and Service Comparison"
        )

        inventory_chart = inventory_df[
            [
                "metric",
                "baseline",
                "optimized",
            ]
        ].copy()

        inventory_chart = inventory_chart.set_index(
            "metric"
        )

        st.bar_chart(
            inventory_chart
        )

    st.subheader(
        "Detailed Business Impact"
    )

    # Round numeric columns.
    display_df = metrics_df.copy()

    for column in [
        "baseline",
        "optimized",
        "change_pct",
    ]:
        if column in display_df.columns:
            display_df[column] = (
                pd.to_numeric(
                    display_df[column],
                    errors="coerce",
                )
                .round(2)
            )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Negative change percentages indicate a reduction from baseline. "
        "Positive service-level change is expressed in percentage points "
        "where shown."
    )


# -------------------------------------------------------------------
# SCENARIO ANALYSIS
# -------------------------------------------------------------------

elif page == "Scenario Analysis":

    st.header(
        "Scenario Analysis"
    )

    growth = st.slider(
        "Demand growth",
        min_value=-0.20,
        max_value=1.00,
        value=0.10,
        step=0.05,
        format="%+.0f%%",
    )

    payload = post_json(
        "/scenario",
        {
            "store_id": store,
            "item_id": item,
            "service_level": service_level,
            "lead_time_days": lead_time,
            "demand_growth": growth,
        },
        timeout=30,
    )

    if payload is None:
        api_error_message()
        st.stop()

    base = payload.get(
        "base",
        {},
    )

    scenario = payload.get(
        "scenario",
        {},
    )

    if not base or not scenario:
        st.warning(
            "Scenario response did not contain both base and scenario results."
        )
        st.stop()

    st.subheader(
        f"{store} × {item}"
    )

    st.caption(
        f"Demand growth scenario: {growth:+.0%}"
    )

    # KPI cards.
    col1, col2, col3, col4 = st.columns(
        4
    )

    with col1:

        base_demand = float(
            base.get(
                "mean_daily_demand",
                0,
            )
        )

        scenario_demand = float(
            scenario.get(
                "mean_daily_demand",
                0,
            )
        )

        st.metric(
            "Mean Daily Demand",
            format_number(
                scenario_demand
            ),
            f"{scenario_demand - base_demand:+.2f}",
        )

    with col2:

        base_ss = float(
            base.get(
                "safety_stock",
                0,
            )
        )

        scenario_ss = float(
            scenario.get(
                "safety_stock",
                0,
            )
        )

        st.metric(
            "Safety Stock",
            format_number(
                scenario_ss
            ),
            f"{scenario_ss - base_ss:+.2f}",
        )

    with col3:

        base_rop = float(
            base.get(
                "reorder_point",
                0,
            )
        )

        scenario_rop = float(
            scenario.get(
                "reorder_point",
                0,
            )
        )

        st.metric(
            "Reorder Point",
            format_number(
                scenario_rop
            ),
            f"{scenario_rop - base_rop:+.2f}",
        )

    with col4:

        base_q = float(
            base.get(
                "order_quantity",
                0,
            )
        )

        scenario_q = float(
            scenario.get(
                "order_quantity",
                0,
            )
        )

        st.metric(
            "Order Quantity",
            format_number(
                scenario_q
            ),
            f"{scenario_q - base_q:+.2f}",
        )

    st.divider()

    # Side-by-side action.
    action_col1, action_col2 = st.columns(
        2
    )

    with action_col1:

        st.subheader(
            "Base Policy"
        )

        display_action(
            base.get(
                "recommended_action",
                "UNKNOWN",
            )
        )

        st.metric(
            "Reorder Point",
            format_number(
                base.get(
                    "reorder_point"
                )
            ),
        )

    with action_col2:

        st.subheader(
            "Scenario Policy"
        )

        display_action(
            scenario.get(
                "recommended_action",
                "UNKNOWN",
            )
        )

        st.metric(
            "Reorder Point",
            format_number(
                scenario.get(
                    "reorder_point"
                )
            ),
        )

    # Comparison table.
    comparison = pd.DataFrame(
        [
            {
                "Metric": "Mean daily demand",
                "Base": base.get(
                    "mean_daily_demand"
                ),
                "Scenario": scenario.get(
                    "mean_daily_demand"
                ),
            },
            {
                "Metric": "Lead-time demand",
                "Base": base.get(
                    "lead_time_demand"
                ),
                "Scenario": scenario.get(
                    "lead_time_demand"
                ),
            },
            {
                "Metric": "Demand std",
                "Base": base.get(
                    "demand_std"
                ),
                "Scenario": scenario.get(
                    "demand_std"
                ),
            },
            {
                "Metric": "Safety stock",
                "Base": base.get(
                    "safety_stock"
                ),
                "Scenario": scenario.get(
                    "safety_stock"
                ),
            },
            {
                "Metric": "Reorder point",
                "Base": base.get(
                    "reorder_point"
                ),
                "Scenario": scenario.get(
                    "reorder_point"
                ),
            },
            {
                "Metric": "Order quantity",
                "Base": base.get(
                    "order_quantity"
                ),
                "Scenario": scenario.get(
                    "order_quantity"
                ),
            },
        ]
    )

    for column in [
        "Base",
        "Scenario",
    ]:

        comparison[column] = (
            pd.to_numeric(
                comparison[column],
                errors="coerce",
            )
            .round(2)
        )

    st.subheader(
        "Base vs Scenario"
    )

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

    # ROP comparison chart.
    rop_chart = pd.DataFrame(
        {
            "Reorder Point": [
                float(
                    base.get(
                        "reorder_point",
                        0,
                    )
                ),
                float(
                    scenario.get(
                        "reorder_point",
                        0,
                    )
                ),
            ]
        },
        index=[
            "Base",
            "Scenario",
        ],
    )

    st.subheader(
        "Reorder Point Comparison"
    )

    st.bar_chart(
        rop_chart
    )

    st.caption(
        f"Scenario demand growth: {scenario.get('scenario_demand_growth', growth):+.0%}"
    )

