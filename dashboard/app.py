
from __future__ import annotations

import os
import time
from typing import Any

import httpx
import streamlit as st


# =====================================================================
# CONFIGURATION
# =====================================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
).rstrip("/")


st.set_page_config(
    page_title="Retail Demand & Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================================
# GLOBAL STYLE
# =====================================================================

CUSTOM_CSS = """
<style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html,
    body,
    [class*="css"] {
        font-family:
            'Inter',
            -apple-system,
            BlinkMacSystemFont,
            sans-serif;
    }

    :root {
        --brand-primary: #1E3A8A;
        --brand-primary-light: #3B5BDB;
        --brand-accent: #0EA5A4;
        --brand-bg: #F7F8FA;
        --brand-surface: #FFFFFF;
        --brand-border: #E5E7EB;
        --brand-text: #111827;
        --brand-muted: #6B7280;

        --success: #15803D;
        --success-bg: #ECFDF3;

        --danger: #B91C1C;
        --danger-bg: #FEF2F2;

        --warning: #B45309;
        --warning-bg: #FFFBEB;
    }


    /* ================================================================
       APP
       ================================================================ */

    .stApp {
        background-color: var(--brand-bg);
    }


    /* ================================================================
       HEADER
       ================================================================ */

    .app-header {
        background:
            linear-gradient(
                120deg,
                var(--brand-primary) 0%,
                var(--brand-primary-light) 100%
            );

        border-radius: 14px;

        padding: 28px 32px;

        margin-bottom: 20px;

        color: white;

        box-shadow:
            0 4px 18px
            rgba(30, 58, 138, 0.18);
    }


    .app-header h1 {
        color: white;

        font-weight: 800;

        font-size: 1.7rem;

        margin:
            0 0 4px 0;

        letter-spacing:
            -0.01em;
    }


    .app-header p {
        color:
            rgba(255, 255, 255, 0.85);

        margin:
            0;

        font-size:
            0.95rem;
    }


    .app-header .badge {
        display:
            inline-block;

        background:
            rgba(255,255,255,0.15);

        border:
            1px solid
            rgba(255,255,255,0.35);

        color:
            white;

        border-radius:
            999px;

        padding:
            3px 12px;

        font-size:
            0.75rem;

        font-weight:
            600;

        margin-top:
            10px;

        letter-spacing:
            0.02em;
    }


    /* ================================================================
       HEADINGS
       ================================================================ */

    h2,
    h3 {
        color:
            var(--brand-text)
            !important;

        font-weight:
            700
            !important;

        letter-spacing:
            -0.01em;
    }


    .section-caption {
        color:
            var(--brand-muted);

        font-size:
            0.92rem;

        margin-top:
            -8px;

        margin-bottom:
            12px;
    }


    /* ================================================================
       METRIC CARDS
       ================================================================ */

    div[data-testid="stMetric"] {
        background:
            var(--brand-surface);

        border:
            1px solid
            var(--brand-border);

        border-radius:
            12px;

        padding:
            16px 18px 12px 18px;

        box-shadow:
            0 1px 3px
            rgba(16, 24, 40, 0.04);
    }


    div[data-testid="stMetricLabel"] {
        color:
            var(--brand-muted);

        font-weight:
            600;

        font-size:
            0.82rem;

        text-transform:
            uppercase;

        letter-spacing:
            0.03em;
    }


    div[data-testid="stMetricValue"] {
        color:
            var(--brand-text);

        font-weight:
            700;
    }


    /* ================================================================
       RECOMMENDATION BANNERS
       ================================================================ */

    .rec-banner {
        border-radius:
            12px;

        padding:
            14px 18px;

        font-weight:
            700;

        font-size:
            1.05rem;

        text-align:
            center;

        border:
            1px solid
            transparent;

        margin-bottom:
            6px;
    }


    .rec-reorder {
        background:
            var(--danger-bg);

        color:
            var(--danger);

        border-color:
            #FCA5A5;
    }


    .rec-hold {
        background:
            var(--success-bg);

        color:
            var(--success);

        border-color:
            #86EFAC;
    }


    .rec-other {
        background:
            var(--warning-bg);

        color:
            var(--warning);

        border-color:
            #FDE68A;
    }


    /* ================================================================
       SIDEBAR
       ================================================================ */

    section[data-testid="stSidebar"] {
        background-color:
            #14213D;
    }


    section[data-testid="stSidebar"] * {
        color:
            #E5E7EB !important;
    }


    section[data-testid="stSidebar"]
    .stSelectbox label,

    section[data-testid="stSidebar"]
    .stSlider label,

    section[data-testid="stSidebar"]
    .stRadio label {
        color:
            #CBD5E1 !important;

        font-weight:
            600;

        font-size:
            0.85rem;
    }


    section[data-testid="stSidebar"] hr {
        border-color:
            rgba(255,255,255,0.12);
    }


    /* ================================================================
       TABLES
       ================================================================ */

    div[data-testid="stTable"] {
        border:
            1px solid
            var(--brand-border);

        border-radius:
            10px;

        overflow:
            hidden;
    }


    /* ================================================================
       FOOTER
       ================================================================ */

    .app-footer {
        margin-top:
            40px;

        padding-top:
            16px;

        border-top:
            1px solid
            var(--brand-border);

        color:
            var(--brand-muted);

        font-size:
            0.8rem;

        text-align:
            center;
    }

</style>
"""


st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True,
)


# =====================================================================
# API HELPERS
# =====================================================================

def api_error_message() -> None:
    """Display a production-friendly API error."""

    st.error(
        "The backend is temporarily unavailable."
    )

    st.caption(
        f"Backend: {API_BASE_URL}"
    )

    st.caption(
        "Please retry in a few seconds."
    )


def request_json(
    method: str,
    endpoint: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 20.0,
    retries: int = 3,
) -> dict[str, Any] | None:
    """Make a resilient API request with retry support."""

    url = (
        f"{API_BASE_URL}{endpoint}"
    )

    last_error: Exception | None = None

    for attempt in range(
        retries
    ):

        try:

            if method.upper() == "GET":

                response = httpx.get(
                    url,
                    timeout=timeout,
                )

            else:

                response = httpx.post(
                    url,
                    json=payload or {},
                    timeout=timeout,
                )

            response.raise_for_status()

            result = response.json()

            if not isinstance(
                result,
                dict,
            ):
                raise ValueError(
                    "API returned an unexpected response format."
                )

            return result

        except Exception as exc:

            last_error = exc

            if attempt < retries - 1:

                time.sleep(
                    1.0
                    * (attempt + 1)
                )

    st.error(
        f"API request failed: {last_error}"
    )

    return None


# =====================================================================
# CACHED API CALLS
# =====================================================================

@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_options() -> dict[str, Any] | None:
    """Cache store/item options for five minutes."""

    return request_json(
        "GET",
        "/options",
        timeout=15,
        retries=3,
    )


@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_business() -> dict[str, Any] | None:
    """Cache business metrics for five minutes."""

    return request_json(
        "GET",
        "/business",
        timeout=15,
        retries=3,
    )


# =====================================================================
# FORMATTING HELPERS
# =====================================================================

def format_number(
    value: Any,
    decimals: int = 2,
) -> str:
    """Format a numeric value."""

    try:

        return (
            f"{float(value):,.{decimals}f}"
        )

    except (
        TypeError,
        ValueError,
    ):

        return "—"


def format_percent(
    value: Any,
    decimals: int = 2,
) -> str:
    """Format a fraction as a percentage."""

    try:

        return (
            f"{float(value) * 100:.{decimals}f}%"
        )

    except (
        TypeError,
        ValueError,
    ):

        return "—"


def percent_change(
    old: Any,
    new: Any,
) -> str | None:
    """Calculate relative percentage change."""

    try:

        old_value = float(old)
        new_value = float(new)

        if old_value == 0:
            return None

        change = (
            (
                new_value
                - old_value
            )
            / old_value
            * 100
        )

        return (
            f"{change:+.2f}%"
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def percentage_point_change(
    old: Any,
    new: Any,
) -> str | None:
    """Calculate percentage-point change."""

    try:

        change = (
            (
                float(new)
                - float(old)
            )
            * 100
        )

        return (
            f"{change:+.2f} pp"
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def get_business_metric(
    metrics: dict[str, Any],
    section: str,
    metric: str,
) -> Any:
    """Retrieve baseline or optimized business metric."""

    block = metrics.get(
        section,
        {},
    )

    if not isinstance(
        block,
        dict,
    ):
        return None

    return block.get(
        metric
    )


def display_action(
    action: Any,
) -> None:
    """Display inventory recommendation."""

    normalized = str(
        action
        if action is not None
        else "UNKNOWN"
    ).upper()

    if normalized == "REORDER":

        st.markdown(
            """
            <div class="rec-banner rec-reorder">
                🔴 REORDER
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif normalized == "HOLD":

        st.markdown(
            """
            <div class="rec-banner rec-hold">
                🟢 HOLD
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            f"""
            <div class="rec-banner rec-other">
                Recommendation: {normalized}
            </div>
            """,
            unsafe_allow_html=True,
        )


def section_intro(
    title: str,
    caption: str | None = None,
) -> None:
    """Render a consistent section heading."""

    st.header(title)

    if caption:

        st.markdown(
            f"""
            <p class="section-caption">
                {caption}
            </p>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================
# APPLICATION HEADER
# =====================================================================

st.markdown(
    """
    <div class="app-header">

        <h1>
            📦 Retail Demand Forecasting &amp;
            Inventory Optimization
        </h1>

        <p>
            Forecast demand, evaluate inventory policies,
            and quantify business impact across your store
            &amp; item portfolio.
        </p>

        <span class="badge">
            LIVE · CONNECTED TO API
        </span>

    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# OPTIONS
# =====================================================================

options_payload = load_options()

if options_payload is None:

    api_error_message()
    st.stop()


options = options_payload.get(
    "options",
    [],
)

if not isinstance(
    options,
    list,
) or not options:

    st.warning(
        "No store/item options are currently available."
    )

    st.stop()


# Native Python sets instead of pandas.
stores = sorted(
    {
        str(row.get("store_id"))
        for row in options
        if isinstance(row, dict)
        and row.get("store_id") is not None
    }
)


if not stores:

    st.error(
        "The API did not return valid store IDs."
    )

    st.stop()


# =====================================================================
# SIDEBAR
# =====================================================================

st.sidebar.markdown(
    "### 📦 Navigator"
)


store = st.sidebar.selectbox(
    "Store ID",
    stores,
)


items = sorted(
    {
        str(row.get("item_id"))
        for row in options
        if isinstance(row, dict)
        and str(row.get("store_id")) == store
        and row.get("item_id") is not None
    }
)


if not items:

    st.error(
        "No items are available for the selected store."
    )

    st.stop()


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


st.sidebar.divider()

st.sidebar.markdown(
    "### ⚙️ Policy Parameters"
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
    f"**API:** {API_BASE_URL}"
)

st.sidebar.caption(
    f"**Store:** {store}"
)

st.sidebar.caption(
    f"**Item:** {item}"
)


# =====================================================================
# EXECUTIVE OVERVIEW
# =====================================================================

if page == "Executive Overview":

    section_intro(
        "Executive Overview",
        "Portfolio-level summary of forecasting and inventory optimization performance.",
    )

    payload = load_business()

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


    metrics = payload.get(
        "metrics",
        {},
    )

    if not isinstance(
        metrics,
        dict,
    ):

        st.warning(
            "Business metrics have an unexpected format."
        )

        st.stop()


    baseline_total = get_business_metric(
        metrics,
        "baseline",
        "total_cost",
    )

    optimized_total = get_business_metric(
        metrics,
        "optimized",
        "total_cost",
    )

    baseline_service = get_business_metric(
        metrics,
        "baseline",
        "service_level",
    )

    optimized_service = get_business_metric(
        metrics,
        "optimized",
        "service_level",
    )

    baseline_inventory = get_business_metric(
        metrics,
        "baseline",
        "average_inventory",
    )

    optimized_inventory = get_business_metric(
        metrics,
        "optimized",
        "average_inventory",
    )


    c1, c2, c3, c4 = st.columns(
        4
    )


    with c1:

        st.metric(
            "Baseline Total Cost",
            format_number(
                baseline_total
            ),
        )


    with c2:

        st.metric(
            "Optimized Total Cost",
            format_number(
                optimized_total
            ),
            percent_change(
                baseline_total,
                optimized_total,
            ),
            delta_color="inverse",
        )


    with c3:

        st.metric(
            "Optimized Service Level",
            format_percent(
                optimized_service
            ),
            percentage_point_change(
                baseline_service,
                optimized_service,
            ),
        )


    with c4:

        st.metric(
            "Average Inventory",
            format_number(
                optimized_inventory
            ),
            percent_change(
                baseline_inventory,
                optimized_inventory,
            ),
            delta_color="inverse",
        )


    st.divider()


    st.subheader(
        "Business Impact"
    )


    # Four headline cards requested for executive view.
    h1, h2, h3, h4 = st.columns(
        4
    )


    with h1:

        st.metric(
            "Total Cost",
            format_number(
                optimized_total
            ),
            percent_change(
                baseline_total,
                optimized_total,
            ),
            delta_color="inverse",
        )


    with h2:

        holding_baseline = get_business_metric(
            metrics,
            "baseline",
            "holding_cost",
        )

        holding_optimized = get_business_metric(
            metrics,
            "optimized",
            "holding_cost",
        )

        st.metric(
            "Holding Cost",
            format_number(
                holding_optimized
            ),
            percent_change(
                holding_baseline,
                holding_optimized,
            ),
            delta_color="inverse",
        )


    with h3:

        stockout_baseline = get_business_metric(
            metrics,
            "baseline",
            "stockout_cost",
        )

        stockout_optimized = get_business_metric(
            metrics,
            "optimized",
            "stockout_cost",
        )

        st.metric(
            "Stockout Cost",
            format_number(
                stockout_optimized
            ),
            percent_change(
                stockout_baseline,
                stockout_optimized,
            ),
            delta_color="inverse",
        )


    with h4:

        st.metric(
            "Service Level",
            format_percent(
                optimized_service
            ),
            percentage_point_change(
                baseline_service,
                optimized_service,
            ),
        )


    st.divider()


    # Cost chart using native dictionaries.
    st.subheader(
        "Cost Comparison"
    )


    cost_chart = {

        "Baseline": {

            "Total Cost": float(
                baseline_total or 0
            ),

            "Holding Cost": float(
                holding_baseline or 0
            ),

            "Ordering Cost": float(
                get_business_metric(
                    metrics,
                    "baseline",
                    "ordering_cost",
                )
                or 0
            ),

            "Stockout Cost": float(
                stockout_baseline or 0
            ),
        },

        "Optimized": {

            "Total Cost": float(
                optimized_total or 0
            ),

            "Holding Cost": float(
                holding_optimized or 0
            ),

            "Ordering Cost": float(
                get_business_metric(
                    metrics,
                    "optimized",
                    "ordering_cost",
                )
                or 0
            ),

            "Stockout Cost": float(
                stockout_optimized or 0
            ),
        },
    }


    # Convert only the small chart structure into the
    # dictionary format Streamlit can consume.
    st.bar_chart(
        {
            category: {
                group: values[group]
                for group in values
            }
            for category, values in cost_chart.items()
            for group in values
        }
    )


    st.subheader(
        "Detailed Business Metrics"
    )


    business_rows = []

    all_metrics = set()

    for block_name in [
        "baseline",
        "optimized",
    ]:

        block = metrics.get(
            block_name,
            {},
        )

        if isinstance(
            block,
            dict,
        ):

            all_metrics.update(
                block.keys()
            )


    for metric_name in sorted(
        all_metrics
    ):

        base_value = get_business_metric(
            metrics,
            "baseline",
            metric_name,
        )

        opt_value = get_business_metric(
            metrics,
            "optimized",
            metric_name,
        )


        if metric_name in {
            "service_level",
            "fill_rate",
        }:

            change = percentage_point_change(
                base_value,
                opt_value,
            )

        else:

            change = percent_change(
                base_value,
                opt_value,
            )


        business_rows.append(
            [
                metric_name.replace(
                    "_",
                    " ",
                ).title(),

                format_number(
                    base_value
                ),

                format_number(
                    opt_value
                ),

                change or "—",
            ]
        )


    st.table(
        {
            "Metric": [
                row[0]
                for row in business_rows
            ],
            "Baseline": [
                row[1]
                for row in business_rows
            ],
            "Optimized": [
                row[2]
                for row in business_rows
            ],
            "Change": [
                row[3]
                for row in business_rows
            ],
        }
    )


# =====================================================================
# DEMAND FORECAST
# =====================================================================

elif page == "Demand Forecast":

    section_intro(
        "Demand Forecast",
        "Model-generated forecast with prediction interval for the selected store and item.",
    )


    horizon = st.slider(
        "Forecast horizon",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
    )


    payload = request_json(
        "POST",
        "/forecast",
        {
            "store_id": store,
            "item_id": item,
            "horizon_days": horizon,
        },
        timeout=30,
        retries=3,
    )


    if payload is None:

        api_error_message()
        st.stop()


    forecasts = payload.get(
        "forecasts",
        [],
    )


    if not isinstance(
        forecasts,
        list,
    ) or not forecasts:

        st.warning(
            "No forecasts were returned."
        )

        st.stop()


    st.subheader(
        f"{store} × {item}"
    )


    c1, c2 = st.columns(
        2
    )


    with c1:

        st.metric(
            "Forecast Model",
            str(
                payload.get(
                    "model_name",
                    "Unknown",
                )
            ),
        )


    with c2:

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


    # Create a compact chart dictionary.
    chart_rows = {}

    for row in forecasts:

        if not isinstance(
            row,
            dict,
        ):
            continue

        date = str(
            row.get(
                "date",
                "",
            )
        )

        if not date:
            continue

        chart_rows[date] = {

            "Forecast": float(
                row.get(
                    "forecast",
                    0,
                )
                or 0
            ),

            "Lower": float(
                row.get(
                    "lower",
                    0,
                )
                or 0
            ),

            "Upper": float(
                row.get(
                    "upper",
                    0,
                )
                or 0
            ),
        }


    if chart_rows:

        st.line_chart(
            chart_rows
        )


    st.subheader(
        "Forecast Table"
    )


    forecast_table = {

        "Date": [],

        "Forecast": [],

        "Lower": [],

        "Upper": [],
    }


    for row in forecasts:

        if not isinstance(
            row,
            dict,
        ):
            continue

        forecast_table["Date"].append(
            str(
                row.get(
                    "date",
                    "",
                )
            )
        )

        forecast_table["Forecast"].append(
            format_number(
                row.get(
                    "forecast"
                )
            )
        )

        forecast_table["Lower"].append(
            format_number(
                row.get(
                    "lower"
                )
            )
        )

        forecast_table["Upper"].append(
            format_number(
                row.get(
                    "upper"
                )
            )
        )


    st.table(
        forecast_table
    )


# =====================================================================
# INVENTORY RECOMMENDATION
# =====================================================================

elif page == "Inventory Recommendation":

    section_intro(
        "Inventory Recommendation",
        "Recommended inventory policy based on service level, demand uncertainty, and lead time.",
    )


    current_inventory = st.number_input(
        "Current inventory",
        min_value=0.0,
        value=20.0,
        step=1.0,
    )


    payload = request_json(
        "POST",
        "/inventory",
        {
            "store_id": store,
            "item_id": item,
            "service_level": service_level,
            "lead_time_days": lead_time,
            "current_inventory": current_inventory,
        },
        timeout=30,
        retries=3,
    )


    if payload is None:

        api_error_message()
        st.stop()


    st.subheader(
        f"{store} × {item}"
    )


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


    c1, c2, c3, c4 = st.columns(
        4
    )


    with c1:

        st.metric(
            "Mean Daily Demand",
            format_number(
                payload.get(
                    "mean_daily_demand"
                )
            ),
        )


    with c2:

        st.metric(
            "Lead-Time Demand",
            format_number(
                payload.get(
                    "lead_time_demand"
                )
            ),
        )


    with c3:

        st.metric(
            "Safety Stock",
            format_number(
                payload.get(
                    "safety_stock"
                )
            ),
        )


    with c4:

        st.metric(
            "Reorder Point",
            format_number(
                payload.get(
                    "reorder_point"
                )
            ),
        )


    c5, c6, c7 = st.columns(
        3
    )


    with c5:

        st.metric(
            "Order Quantity",
            format_number(
                payload.get(
                    "order_quantity"
                )
            ),
        )


    with c6:

        st.metric(
            "Current Inventory",
            format_number(
                payload.get(
                    "current_inventory"
                )
            ),
        )


    with c7:

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


    st.subheader(
        "Inventory Policy Details"
    )


    inventory_table = {

        "Metric": [
            "Mean daily demand",
            "Lead-time demand",
            "Demand standard deviation",
            "Safety stock",
            "Reorder point",
            "Order quantity",
        ],

        "Value": [
            format_number(
                payload.get(
                    "mean_daily_demand"
                )
            ),

            format_number(
                payload.get(
                    "lead_time_demand"
                )
            ),

            format_number(
                payload.get(
                    "demand_std"
                ),
                3,
            ),

            format_number(
                payload.get(
                    "safety_stock"
                )
            ),

            format_number(
                payload.get(
                    "reorder_point"
                )
            ),

            format_number(
                payload.get(
                    "order_quantity"
                )
            ),
        ],
    }


    st.table(
        inventory_table
    )


    st.caption(
        f"Model: {payload.get('model_name', 'Unknown')}"
    )


# =====================================================================
# BUSINESS IMPACT
# =====================================================================

elif page == "Business Impact":

    section_intro(
        "Business Impact",
        "Baseline versus optimized inventory-policy performance.",
    )


    payload = load_business()


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


    metrics = payload.get(
        "metrics",
        {},
    )


    if not isinstance(
        metrics,
        dict,
    ):

        st.warning(
            "No structured business metrics were returned."
        )

        st.stop()


    baseline_total = get_business_metric(
        metrics,
        "baseline",
        "total_cost",
    )

    optimized_total = get_business_metric(
        metrics,
        "optimized",
        "total_cost",
    )

    baseline_holding = get_business_metric(
        metrics,
        "baseline",
        "holding_cost",
    )

    optimized_holding = get_business_metric(
        metrics,
        "optimized",
        "holding_cost",
    )

    baseline_stockout = get_business_metric(
        metrics,
        "baseline",
        "stockout_cost",
    )

    optimized_stockout = get_business_metric(
        metrics,
        "optimized",
        "stockout_cost",
    )

    baseline_service = get_business_metric(
        metrics,
        "baseline",
        "service_level",
    )

    optimized_service = get_business_metric(
        metrics,
        "optimized",
        "service_level",
    )


    c1, c2, c3, c4 = st.columns(
        4
    )


    with c1:

        st.metric(
            "Total Cost",
            format_number(
                optimized_total
            ),
            percent_change(
                baseline_total,
                optimized_total,
            ),
            delta_color="inverse",
        )


    with c2:

        st.metric(
            "Holding Cost",
            format_number(
                optimized_holding
            ),
            percent_change(
                baseline_holding,
                optimized_holding,
            ),
            delta_color="inverse",
        )


    with c3:

        st.metric(
            "Stockout Cost",
            format_number(
                optimized_stockout
            ),
            percent_change(
                baseline_stockout,
                optimized_stockout,
            ),
            delta_color="inverse",
        )


    with c4:

        st.metric(
            "Service Level",
            format_percent(
                optimized_service
            ),
            percentage_point_change(
                baseline_service,
                optimized_service,
            ),
        )


    st.divider()


    st.subheader(
        "Cost Comparison"
    )


    # Native list structure for chart data.
    cost_chart = {

        "Baseline": [
            float(
                baseline_total or 0
            ),

            float(
                baseline_holding or 0
            ),

            float(
                get_business_metric(
                    metrics,
                    "baseline",
                    "ordering_cost",
                )
                or 0
            ),

            float(
                baseline_stockout or 0
            ),
        ],

        "Optimized": [
            float(
                optimized_total or 0
            ),

            float(
                optimized_holding or 0
            ),

            float(
                get_business_metric(
                    metrics,
                    "optimized",
                    "ordering_cost",
                )
                or 0
            ),

            float(
                optimized_stockout or 0
            ),
        ],
    }


    st.bar_chart(
        cost_chart
    )


    st.subheader(
        "Inventory & Service Metrics"
    )


    inventory_chart = {

        "Baseline": [
            float(
                get_business_metric(
                    metrics,
                    "baseline",
                    "average_inventory",
                )
                or 0
            ),

            float(
                get_business_metric(
                    metrics,
                    "baseline",
                    "stockout_units",
                )
                or 0
            ),

            float(
                get_business_metric(
                    metrics,
                    "baseline",
                    "orders",
                )
                or 0
            ),
        ],

        "Optimized": [
            float(
                get_business_metric(
                    metrics,
                    "optimized",
                    "average_inventory",
                )
                or 0
            ),

            float(
                get_business_metric(
                    metrics,
                    "optimized",
                    "stockout_units",
                )
                or 0
            ),

            float(
                get_business_metric(
                    metrics,
                    "optimized",
                    "orders",
                )
                or 0
            ),
        ],
    }


    st.bar_chart(
        inventory_chart
    )


    st.subheader(
        "Detailed Business Impact"
    )


    business_rows = []

    metric_names = set()

    for block_name in [
        "baseline",
        "optimized",
    ]:

        block = metrics.get(
            block_name,
            {},
        )

        if isinstance(
            block,
            dict,
        ):

            metric_names.update(
                block.keys()
            )


    for metric_name in sorted(
        metric_names
    ):

        baseline_value = get_business_metric(
            metrics,
            "baseline",
            metric_name,
        )

        optimized_value = get_business_metric(
            metrics,
            "optimized",
            metric_name,
        )


        if metric_name in {
            "service_level",
            "fill_rate",
        }:

            change = percentage_point_change(
                baseline_value,
                optimized_value,
            )

        else:

            change = percent_change(
                baseline_value,
                optimized_value,
            )


        business_rows.append(
            {
                "Metric":
                    metric_name.replace(
                        "_",
                        " ",
                    ).title(),

                "Baseline":
                    format_number(
                        baseline_value
                    ),

                "Optimized":
                    format_number(
                        optimized_value
                    ),

                "Change":
                    change or "—",
            }
        )


    # st.table accepts a list of dictionaries.
    st.table(
        business_rows
    )


    st.caption(
        "Negative cost changes indicate a reduction from baseline. "
        "Service-level changes are shown in percentage points."
    )


# =====================================================================
# SCENARIO ANALYSIS
# =====================================================================

elif page == "Scenario Analysis":

    section_intro(
        "Scenario Analysis",
        "Stress-test the selected inventory policy against a demand-growth scenario.",
    )


    growth = st.slider(
        "Demand growth",
        min_value=-0.20,
        max_value=1.00,
        value=0.10,
        step=0.05,
        format="%+.0f%%",
    )


    payload = request_json(
        "POST",
        "/scenario",
        {
            "store_id": store,
            "item_id": item,
            "service_level": service_level,
            "lead_time_days": lead_time,
            "demand_growth": growth,
        },
        timeout=30,
        retries=3,
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


    if not isinstance(
        base,
        dict,
    ) or not isinstance(
        scenario,
        dict,
    ):

        st.warning(
            "Scenario response is incomplete."
        )

        st.stop()


    st.subheader(
        f"{store} × {item}"
    )


    st.caption(
        f"Demand growth scenario: {growth:+.0%}"
    )


    c1, c2, c3, c4 = st.columns(
        4
    )


    with c1:

        st.metric(
            "Mean Daily Demand",
            format_number(
                scenario.get(
                    "mean_daily_demand"
                )
            ),
            format_number(
                float(
                    scenario.get(
                        "mean_daily_demand",
                        0,
                    )
                    or 0
                )
                -
                float(
                    base.get(
                        "mean_daily_demand",
                        0,
                    )
                    or 0
                )
            ),
        )


    with c2:

        st.metric(
            "Safety Stock",
            format_number(
                scenario.get(
                    "safety_stock"
                )
            ),
            format_number(
                float(
                    scenario.get(
                        "safety_stock",
                        0,
                    )
                    or 0
                )
                -
                float(
                    base.get(
                        "safety_stock",
                        0,
                    )
                    or 0
                )
            ),
        )


    with c3:

        st.metric(
            "Reorder Point",
            format_number(
                scenario.get(
                    "reorder_point"
                )
            ),
            format_number(
                float(
                    scenario.get(
                        "reorder_point",
                        0,
                    )
                    or 0
                )
                -
                float(
                    base.get(
                        "reorder_point",
                        0,
                    )
                    or 0
                )
            ),
        )


    with c4:

        st.metric(
            "Order Quantity",
            format_number(
                scenario.get(
                    "order_quantity"
                )
            ),
            format_number(
                float(
                    scenario.get(
                        "order_quantity",
                        0,
                    )
                    or 0
                )
                -
                float(
                    base.get(
                        "order_quantity",
                        0,
                    )
                    or 0
                )
            ),
        )


    st.divider()


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


    st.subheader(
        "Base vs Scenario"
    )


    comparison_rows = []


    for metric_name in [
        "mean_daily_demand",
        "lead_time_demand",
        "demand_std",
        "safety_stock",
        "reorder_point",
        "order_quantity",
    ]:

        comparison_rows.append(
            {
                "Metric":
                    metric_name.replace(
                        "_",
                        " ",
                    ).title(),

                "Base":
                    format_number(
                        base.get(
                            metric_name
                        )
                    ),

                "Scenario":
                    format_number(
                        scenario.get(
                            metric_name
                        )
                    ),
            }
        )


    st.table(
        comparison_rows
    )


    st.subheader(
        "Reorder Point Comparison"
    )


    st.bar_chart(
        {
            "Base": [
                float(
                    base.get(
                        "reorder_point",
                        0,
                    )
                    or 0
                )
            ],

            "Scenario": [
                float(
                    scenario.get(
                        "reorder_point",
                        0,
                    )
                    or 0
                )
            ],
        }
    )


    st.caption(
        "Scenario analysis applies the selected demand-growth assumption "
        "to the base inventory recommendation."
    )


# =====================================================================
# FOOTER
# =====================================================================

st.markdown(
    f"""
    <div class="app-footer">
        Retail Demand Forecasting &amp; Inventory Optimization
        · Connected to {API_BASE_URL}
    </div>
    """,
    unsafe_allow_html=True,
)
