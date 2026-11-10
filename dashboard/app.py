from __future__ import annotations

import json
import os
from statistics import NormalDist
from typing import Any

import httpx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://retail-demand-inventory-optimization.onrender.com",
).rstrip("/")
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


st.set_page_config(
    page_title="Retail Intelligence | Demand & Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
      :root { --bg:#080d14; --panel:#101824; --panel2:#131f2d; --line:#233244;
              --muted:#8fa1b5; --text:#e7eef7; --green:#57d68d; --cyan:#52c7df;
              --orange:#f2b766; --red:#ff747c; }
      .stApp { background:radial-gradient(ellipse at 18% 0%,#142337 0%,#080d14 42%); color:var(--text); }
      html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
      [data-testid="stSidebar"] { background:#0b121c; border-right:1px solid var(--line); }
      [data-testid="stSidebar"] * { color:#dce6f1; }
      .block-container { padding-top:1.2rem; max-width:1600px; }
      h1,h2,h3 { letter-spacing:-.04em; }
      h1 { font-size:1.8rem !important; font-weight:800 !important; }
      h2 { font-size:1.18rem !important; font-weight:750 !important; }
      h3 { font-size:1rem !important; font-weight:700 !important; }
      [data-testid="stMetric"] { background:linear-gradient(145deg,#142131,#0e1722);
        border:1px solid #26384b; border-radius:13px; padding:15px 16px; }
      [data-testid="stMetricLabel"] { color:#9badc0 !important; font-size:.78rem; }
      [data-testid="stMetricValue"] { color:#f2f7fc !important; font-weight:800; }
      [data-testid="stMetricDelta"] { font-family:'DM Mono',monospace; }
      div[data-testid="stPlotlyChart"] { background:rgba(16,24,36,.72); border:1px solid #223246;
        border-radius:13px; padding:7px; }
      div[data-testid="stDataFrame"] { border:1px solid #26384b; border-radius:10px; }
      .eyebrow { color:#68cfe0; font:500 .68rem 'DM Mono',monospace; letter-spacing:.16em; }
      .hero { padding:5px 0 14px 0; }
      .hero-sub { color:#94a8bc; font-size:.88rem; margin-top:-7px; }
      .section-note { color:#8fa1b5; font-size:.78rem; }
      .status-pill { display:inline-block; padding:4px 9px; border-radius:99px;
        background:#123326; border:1px solid #245b42; color:#73e4a5; font:500 .68rem 'DM Mono',monospace; }
      .small-mono { color:#90a4b8; font: .7rem 'DM Mono',monospace; }
      hr { border-color:#26384b !important; }
      button[kind="secondary"] { border-color:#2a4056; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Cache pure API reads and deterministic calculations. The cache is bounded
# and short-lived so the dashboard does not repeatedly scan Parquet or infer.
@st.cache_data(ttl=600, max_entries=8, show_spinner=False)
def load_options() -> dict[str, Any]:
    response = httpx.get(f"{API_BASE_URL}/options", timeout=8.0)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=180, max_entries=256, show_spinner=False)
def load_series(store_id: str, item_id: str) -> dict[str, Any]:
    response = httpx.get(
        f"{API_BASE_URL}/series",
        params={"store_id": store_id, "item_id": item_id},
        timeout=8.0,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, max_entries=8, show_spinner=False)
def load_business() -> dict[str, Any]:
    response = httpx.get(f"{API_BASE_URL}/business", timeout=8.0)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, max_entries=256, show_spinner=False)
def load_forecast(store_id: str, item_id: str, horizon: int) -> dict[str, Any]:
    response = httpx.post(
        f"{API_BASE_URL}/forecast",
        json={"store_id": store_id, "item_id": item_id, "horizon_days": horizon},
        timeout=25.0,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120, max_entries=512, show_spinner=False)
def load_inventory(
    store_id: str, item_id: str, service_level: float,
    lead_time: int, current_inventory: float,
) -> dict[str, Any]:
    response = httpx.post(
        f"{API_BASE_URL}/inventory",
        json={
            "store_id": store_id, "item_id": item_id,
            "service_level": service_level, "lead_time_days": lead_time,
            "current_inventory": current_inventory,
        },
        timeout=8.0,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120, max_entries=512, show_spinner=False)
def load_scenario(
    store_id: str, item_id: str, service_level: float,
    lead_time: int, demand_growth: float,
) -> dict[str, Any]:
    response = httpx.post(
        f"{API_BASE_URL}/scenario",
        json={
            "store_id": store_id, "item_id": item_id,
            "service_level": service_level, "lead_time_days": lead_time,
            "demand_growth": demand_growth,
        },
        timeout=8.0,
    )
    response.raise_for_status()
    return response.json()


def money(value: Any) -> str:
    try:
        return f"{float(value):,.1f}"
    except (TypeError, ValueError):
        return "—"


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def metric_value(metrics: dict[str, Any], name: str, group: str) -> float | None:
    try:
        return float(metrics[group][name])
    except (KeyError, TypeError, ValueError):
        return None


def plot_layout(fig: go.Figure, height: int = 330, legend: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=18, r=18, t=32, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#b9c8d8", size=11),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
        ) if legend else dict(visible=False),
        hoverlabel=dict(bgcolor="#172536", bordercolor="#38506a"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#2a3a4c")
    fig.update_yaxes(gridcolor="rgba(115,139,163,.13)", zeroline=False)
    return fig


def card_title(title: str, note: str | None = None) -> None:
    st.markdown(f"**{title}**", help=note)


def make_history_frame(payload: dict[str, Any]) -> pd.DataFrame:
    frame = pd.DataFrame(payload.get("history", []))
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    frame["demand"] = pd.to_numeric(frame["demand"], errors="coerce").fillna(0.0)
    if "sell_price" in frame:
        frame["sell_price"] = pd.to_numeric(frame["sell_price"], errors="coerce")
    return frame.sort_values("date").reset_index(drop=True)


def render_overview(history: pd.DataFrame, store: str, item: str) -> None:
    st.markdown('<div class="eyebrow">PORTFOLIO MONITOR / SERIES VIEW</div>', unsafe_allow_html=True)
    st.header("Demand & inventory command centre")
    st.markdown(
        f'<div class="hero-sub">Selected series · <b>{store}</b> / <b>{item}</b> · '
        f'Latest {len(history)} observations</div>',
        unsafe_allow_html=True,
    )

    demand = history["demand"]
    avg = float(demand.mean())
    std = float(demand.std(ddof=1)) if len(demand) > 1 else 0.0
    previous = float(demand.iloc[:-28].tail(28).mean()) if len(demand) > 28 else avg
    recent = float(demand.tail(28).mean())
    trend = ((recent / previous) - 1) * 100 if previous else 0.0
    cv = std / avg if avg else 0.0
    total = float(demand.sum())
    price = history["sell_price"].dropna().iloc[-1] if "sell_price" in history and history["sell_price"].notna().any() else None

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Units · history window", money(total), "observed demand")
    k2.metric("Daily run rate", money(avg), "units / day")
    k3.metric("Demand volatility", pct(cv), "coefficient of variation")
    k4.metric("28-day demand trend", f"{trend:+.1f}%", "recent vs prior period")
    k5.metric("Latest selling price", money(price), "source price" if price is not None else "not available")

    left, right = st.columns([1.65, 1])
    with left:
        card_title("Demand trajectory", "Observed demand and trailing seven-day average.")
        trend_df = history[["date", "demand"]].copy()
        trend_df["7-day mean"] = trend_df["demand"].rolling(7, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["demand"], name="Actual demand",
            mode="lines", line=dict(color="#56c9df", width=1.5),
        ))
        fig.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["7-day mean"], name="7-day rolling mean",
            mode="lines", line=dict(color="#f0b66b", width=2.5),
        ))
        st.plotly_chart(plot_layout(fig, 350), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Demand distribution", "Empirical distribution of observed daily demand.")
        fig = px.histogram(history, x="demand", nbins=22, marginal="box",
                          color_discrete_sequence=["#59cbe0"])
        fig.update_traces(opacity=.82)
        st.plotly_chart(plot_layout(fig, 350, legend=False), use_container_width=True, config=PLOT_CONFIG)

    left, right = st.columns(2)
    with left:
        card_title("Weekly seasonality", "Mean observed demand by day of week.")
        season = history.assign(weekday=history["date"].dt.day_name()).groupby("weekday", as_index=False)["demand"].mean()
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        season["weekday"] = pd.Categorical(season["weekday"], categories=order, ordered=True)
        season = season.sort_values("weekday")
        fig = px.bar(season, x="weekday", y="demand", color="demand",
                     color_continuous_scale=["#17384b", "#52c7df"])
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(plot_layout(fig, 290, legend=False), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Demand stability", "Rolling 7-day standard deviation.")
        stability = history[["date", "demand"]].copy()
        stability["rolling_std"] = stability["demand"].rolling(7, min_periods=3).std()
        fig = px.area(stability, x="date", y="rolling_std",
                      color_discrete_sequence=["#b58ae8"])
        st.plotly_chart(plot_layout(fig, 290, legend=False), use_container_width=True, config=PLOT_CONFIG)


def render_forecast(history: pd.DataFrame, store: str, item: str) -> None:
    st.markdown('<div class="eyebrow">PREDICTIVE INTELLIGENCE / TIME SERIES</div>', unsafe_allow_html=True)
    st.header("Demand forecasting")
    horizon = st.select_slider("Forecast horizon", options=[7, 14, 21, 28, 56], value=14)
    try:
        with st.spinner("Generating forecast…"):
            payload = load_forecast(store, item, int(horizon))
    except Exception as exc:
        st.error(f"Forecast service unavailable: {exc}")
        return
    forecast = pd.DataFrame(payload.get("forecasts", []))
    if forecast.empty:
        st.warning("No forecast points returned.")
        return
    forecast["date"] = pd.to_datetime(forecast["date"])
    forecast = forecast.sort_values("date")

    a, b, c = st.columns(3)
    a.metric("Forecast horizon", f"{len(forecast)} days")
    b.metric("Forecast demand", money(forecast["forecast"].sum()), "cumulative units")
    c.metric("Residual standard deviation", money(payload.get("residual_std")), "model residual scale")

    card_title("Actual vs forecast · uncertainty envelope")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history["date"], y=history["demand"], name="Observed",
        line=dict(color="#56c9df", width=1.8),
    ))
    fig.add_trace(go.Scatter(
        x=forecast["date"], y=forecast["upper"], name="Upper interval",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["date"], y=forecast["lower"], name="Prediction interval",
        fill="tonexty", fillcolor="rgba(83,198,222,.15)",
        line=dict(width=0), hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["date"], y=forecast["forecast"], name="Forecast",
        line=dict(color="#f0b66b", width=2.8),
    ))
    fig.add_vline(x=history["date"].max().timestamp() * 1000, line_dash="dot",
                  line_color="#8296aa", opacity=.7)
    st.plotly_chart(plot_layout(fig, 410), use_container_width=True, config=PLOT_CONFIG)

    left, right = st.columns(2)
    with left:
        card_title("Daily forecast profile")
        fig = px.bar(forecast, x="date", y="forecast",
                     color="forecast", color_continuous_scale=["#18384c", "#58cce1"])
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(plot_layout(fig, 290, legend=False), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Forecast interval width")
        forecast["interval_width"] = forecast["upper"] - forecast["lower"]
        fig = px.area(forecast, x="date", y="interval_width",
                      color_discrete_sequence=["#b58ae8"])
        st.plotly_chart(plot_layout(fig, 290, legend=False), use_container_width=True, config=PLOT_CONFIG)

    with st.expander("Inspect forecast values"):
        st.dataframe(forecast.round(2), use_container_width=True, hide_index=True)


def render_inventory(history: pd.DataFrame, store: str, item: str,
                     service_level: float, lead_time: int) -> None:
    st.markdown('<div class="eyebrow">DECISION SCIENCE / PERIODIC REVIEW</div>', unsafe_allow_html=True)
    st.header("Inventory control tower")
    current = st.number_input("On-hand inventory (units)", min_value=0.0, value=20.0, step=1.0)
    try:
        with st.spinner("Calculating replenishment policy…"):
            result = load_inventory(store, item, service_level, lead_time, current)
    except Exception as exc:
        st.error(f"Inventory service unavailable: {exc}")
        return

    reorder = float(result["reorder_point"])
    action = str(result["recommended_action"]).upper()
    status_color = "#57d68d" if action == "HOLD" else "#ff747c"
    st.markdown(
        f'<div style="padding:13px 16px;border:1px solid {status_color};border-radius:12px;'
        f'background:rgba(20,35,48,.8);margin:8px 0 18px 0;">'
        f'<span class="small-mono">REPLENISHMENT DECISION</span><br>'
        f'<b style="font-size:1.25rem;color:{status_color}">{action}</b>'
        f'<span style="color:#9badc0;margin-left:12px">Stock position {current:,.0f} / reorder point {reorder:,.1f}</span></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reorder point", money(reorder), "units")
    c2.metric("Safety stock", money(result["safety_stock"]), "buffer units")
    c3.metric("Lead-time demand", money(result["lead_time_demand"]), "expected units")
    c4.metric("Suggested order", money(result["order_quantity"]), "units")

    left, right = st.columns([1, 1.35])
    with left:
        card_title("Stock position gauge")
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=float(current),
            number={"font": {"color": "#e7eef7"}},
            gauge={
                "axis": {"range": [0, max(reorder * 1.5, current * 1.2, 1)]},
                "bar": {"color": status_color},
                "bgcolor": "#152233",
                "bordercolor": "#304459",
                "steps": [
                    {"range": [0, reorder], "color": "rgba(255,116,124,.16)"},
                    {"range": [reorder, max(reorder * 1.5, current * 1.2, 1)], "color": "rgba(87,214,141,.12)"},
                ],
                "threshold": {"line": {"color": "#f0b66b", "width": 3}, "value": reorder},
            },
        ))
        st.plotly_chart(plot_layout(fig, 280, legend=False), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Reorder point composition")
        fig = go.Figure(go.Waterfall(
            x=["Lead-time demand", "Safety stock", "Reorder point"],
            y=[float(result["lead_time_demand"]), float(result["safety_stock"]), 0],
            measure=["relative", "relative", "total"],
            text=[money(result["lead_time_demand"]), money(result["safety_stock"]), money(reorder)],
            textposition="outside",
            connector={"line": {"color": "#53687d"}},
            increasing={"marker": {"color": "#55c8df"}},
            totals={"marker": {"color": "#f0b66b"}},
        ))
        st.plotly_chart(plot_layout(fig, 280, legend=False), use_container_width=True, config=PLOT_CONFIG)

    st.subheader("Service-level sensitivity")
    std = float(result["demand_std"])
    mean = float(result["mean_daily_demand"])
    levels = np.array([.80, .85, .90, .92, .95, .97, .99])
    z_values = np.array([NormalDist().inv_cdf(float(level)) for level in levels])
    safety = std * np.sqrt(max(lead_time, 1)) * z_values
    sensitivity = pd.DataFrame({
        "Service level": levels,
        "Safety stock": safety,
        "Reorder point": mean * lead_time + safety,
    })
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sensitivity["Service level"], y=sensitivity["Reorder point"],
                             mode="lines+markers", name="Reorder point",
                             line=dict(color="#56c9df", width=2.5)))
    fig.add_trace(go.Scatter(x=sensitivity["Service level"], y=sensitivity["Safety stock"],
                             mode="lines+markers", name="Safety stock",
                             line=dict(color="#b58ae8", width=2)))
    st.plotly_chart(plot_layout(fig, 300), use_container_width=True, config=PLOT_CONFIG)
    st.caption("Sensitivity curve uses a normal-demand approximation for explanation; it is not a fresh inventory simulation.")
    with st.expander("Inventory policy details"):
        st.json(result)


def render_business() -> None:
    st.markdown('<div class="eyebrow">OPERATIONS RESEARCH / ECONOMIC EVALUATION</div>', unsafe_allow_html=True)
    st.header("Business impact analytics")
    try:
        payload = load_business()
    except Exception as exc:
        st.error(f"Business metrics unavailable: {exc}")
        return
    if not payload.get("available"):
        st.info(payload.get("notes", "Run the inventory simulation and business-impact pipeline to populate this page."))
        return
    metrics = payload.get("metrics", {})
    baseline = metrics.get("baseline", {})
    optimized = metrics.get("optimized", {})
    if not baseline or not optimized:
        st.warning("Business summary has no baseline/optimized comparison.")
        return

    base_cost = metric_value(metrics, "total_cost", "baseline")
    opt_cost = metric_value(metrics, "total_cost", "optimized")
    savings = ((base_cost - opt_cost) / base_cost * 100) if base_cost else None
    service = metric_value(metrics, "service_level", "optimized")
    fill = metric_value(metrics, "fill_rate", "optimized")
    stockouts = metric_value(metrics, "stockout_units", "optimized")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Simulated cost reduction", f"{savings:.1f}%" if savings is not None else "—")
    c2.metric("Optimized service level", pct(service))
    c3.metric("Optimized fill rate", pct(fill))
    c4.metric("Stockout units", money(stockouts))

    compare_names = ["total_cost", "holding_cost", "ordering_cost", "stockout_cost"]
    rows = []
    for name in compare_names:
        if name in baseline and name in optimized:
            rows.extend([
                {"Cost component": name.replace("_", " ").title(), "Policy": "Baseline", "Cost": float(baseline[name])},
                {"Cost component": name.replace("_", " ").title(), "Policy": "Optimized", "Cost": float(optimized[name])},
            ])
    if rows:
        left, right = st.columns([1.4, 1])
        with left:
            card_title("Cost decomposition · baseline vs optimized")
            fig = px.bar(pd.DataFrame(rows), x="Cost component", y="Cost", color="Policy",
                         barmode="group", color_discrete_map={"Baseline": "#73869a", "Optimized": "#55c8df"})
            st.plotly_chart(plot_layout(fig, 350), use_container_width=True, config=PLOT_CONFIG)
        with right:
            card_title("Optimized cost mix")
            labels = ["holding_cost", "ordering_cost", "stockout_cost"]
            values = [float(optimized.get(x, 0) or 0) for x in labels]
            fig = go.Figure(go.Pie(
                labels=[x.replace("_", " ").title() for x in labels],
                values=values, hole=.62,
                marker={"colors": ["#55c8df", "#f0b66b", "#b58ae8"]},
                textinfo="label+percent",
            ))
            st.plotly_chart(plot_layout(fig, 350, legend=False), use_container_width=True, config=PLOT_CONFIG)

    operational = ["average_inventory", "stockout_units", "service_level", "fill_rate"]
    op_rows = []
    for name in operational:
        if name in baseline and name in optimized:
            op_rows.append({
                "Metric": name.replace("_", " ").title(),
                "Baseline": float(baseline[name]),
                "Optimized": float(optimized[name]),
            })
    if op_rows:
        card_title("Operational performance")
        frame = pd.DataFrame(op_rows).set_index("Metric")
        st.plotly_chart(plot_layout(go.Figure([
            go.Bar(name="Baseline", x=frame.index, y=frame["Baseline"], marker_color="#73869a"),
            go.Bar(name="Optimized", x=frame.index, y=frame["Optimized"], marker_color="#55c8df"),
        ]).update_layout(barmode="group"), 330), use_container_width=True, config=PLOT_CONFIG)

    st.caption("These are offline simulation results under configured cost assumptions—not realized retailer savings.")
    with st.expander("Full business metrics"):
        st.dataframe(pd.DataFrame([
            {"Metric": k, "Baseline": baseline.get(k), "Optimized": optimized.get(k)}
            for k in sorted(set(baseline) | set(optimized))
        ]), use_container_width=True, hide_index=True)


def render_scenario(store: str, item: str, service_level: float, lead_time: int) -> None:
    st.markdown('<div class="eyebrow">WHAT-IF MODELLING / DECISION SUPPORT</div>', unsafe_allow_html=True)
    st.header("Scenario studio")
    st.caption("Explore how demand growth changes replenishment targets. Results are policy calculations, not a re-run of the full event simulator.")
    growth = st.slider("Demand growth assumption", min_value=-30, max_value=150, value=20, step=5, format="%d%%") / 100
    try:
        with st.spinner("Evaluating scenario…"):
            payload = load_scenario(store, item, service_level, lead_time, float(growth))
    except Exception as exc:
        st.error(f"Scenario service unavailable: {exc}")
        return
    base, scenario = payload["base"], payload["scenario"]
    base_rop = float(base["reorder_point"])
    scenario_rop = float(scenario["reorder_point"])
    delta = scenario_rop - base_rop
    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline reorder point", money(base_rop))
    c2.metric("Scenario reorder point", money(scenario_rop), f"{delta:+,.1f} units")
    c3.metric("Demand growth", f"{growth:+.0%}")
    comparison = pd.DataFrame([
        {"Metric": "Mean daily demand", "Baseline": base["mean_daily_demand"], "Scenario": scenario["mean_daily_demand"]},
        {"Metric": "Lead-time demand", "Baseline": base["lead_time_demand"], "Scenario": scenario["lead_time_demand"]},
        {"Metric": "Safety stock", "Baseline": base["safety_stock"], "Scenario": scenario["safety_stock"]},
        {"Metric": "Reorder point", "Baseline": base_rop, "Scenario": scenario_rop},
        {"Metric": "Order quantity", "Baseline": base["order_quantity"], "Scenario": scenario["order_quantity"]},
    ])
    card_title("Decision variable comparison")
    melted = comparison.melt(id_vars="Metric", var_name="Scenario", value_name="Units")
    fig = px.bar(melted, x="Metric", y="Units", color="Scenario", barmode="group",
                 color_discrete_map={"Baseline": "#73869a", "Scenario": "#55c8df"})
    st.plotly_chart(plot_layout(fig, 350), use_container_width=True, config=PLOT_CONFIG)
    st.dataframe(comparison.round(2), use_container_width=True, hide_index=True)


# ------------------------------ SIDEBAR ------------------------------
with st.sidebar:
    st.markdown("## ◈ RETAIL / INTEL")
    st.markdown('<span class="small-mono">DEMAND & INVENTORY PLATFORM</span>', unsafe_allow_html=True)
    st.divider()
    try:
        options_payload = load_options()
        options = options_payload.get("options", [])
        pairs = pd.DataFrame(options)
        if pairs.empty or not {"store_id", "item_id"}.issubset(pairs.columns):
            st.error("No valid store/item options. Run the data pipeline first.")
            st.stop()
        pairs["store_id"] = pairs["store_id"].astype(str)
        pairs["item_id"] = pairs["item_id"].astype(str)
    except Exception as exc:
        st.error(f"Cannot connect to the API: {exc}")
        st.caption(f"API endpoint: {API_BASE_URL}")
        st.stop()

    stores = sorted(pairs["store_id"].unique())
    store = st.selectbox("STORE", stores, key="selected_store")
    items = sorted(pairs.loc[pairs["store_id"] == store, "item_id"].unique())
    item = st.selectbox("SKU / ITEM", items, key=f"item_{store}")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Demand Forecast", "Inventory Control", "Business Impact", "Scenario Studio"],
        label_visibility="collapsed",
    )
    service_level = st.slider("Target service level", .80, .99, .90, .01, format="%.0f%%")
    lead_time = st.slider("Supplier lead time · days", 1, 30, 7)
    st.divider()
    st.markdown('<span class="status-pill">● API CONNECTED</span>', unsafe_allow_html=True)
    st.caption(f"Selected: {store} · {item}")
    st.caption(f"Endpoint: {API_BASE_URL}")


# ------------------------------ MAIN VIEW ------------------------------
st.markdown(
    f'<div class="hero"><div class="eyebrow">RETAIL INTELLIGENCE PLATFORM / LIVE WORKSPACE</div>'
    f'<h1 style="margin:5px 0 2px 0">Retail Demand & Inventory Intelligence</h1>'
    f'<div class="hero-sub">Decision support for demand planning, inventory risk and operating economics.</div></div>',
    unsafe_allow_html=True,
)
try:
    with st.spinner("Loading selected demand series…"):
        history_payload = load_series(store, item)
    history = make_history_frame(history_payload)
except Exception as exc:
    st.error(f"Could not load selected series: {exc}")
    st.stop()

if history.empty:
    st.warning("No observations are available for this store-item series.")
    st.stop()

if page == "Overview":
    render_overview(history, store, item)
elif page == "Demand Forecast":
    render_forecast(history, store, item)
elif page == "Inventory Control":
    render_inventory(history, store, item, service_level, lead_time)
elif page == "Business Impact":
    render_business()
else:
    render_scenario(store, item, service_level, lead_time)

st.markdown("---")
st.markdown(
    f'<span class="small-mono">DATA WINDOW: {history["date"].min().date()} → {history["date"].max().date()}'
    f' &nbsp; · &nbsp; SERIES OBSERVATIONS: {len(history)}'
    f' &nbsp; · &nbsp; API: {API_BASE_URL}</span>',
    unsafe_allow_html=True,
)
