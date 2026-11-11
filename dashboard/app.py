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
      [data-testid="stSidebar"] {
        background:
          radial-gradient(ellipse at 8% 0%, rgba(41,102,133,.22), transparent 38%),
          linear-gradient(180deg,#0d1724 0%,#09111b 62%,#080e17 100%);
        border-right:1px solid #26394e;
      }
      [data-testid="stSidebar"] > div:first-child { padding-top:1.25rem; }
      [data-testid="stSidebar"] * { color:#dce6f1; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        font-size:1.12rem !important; letter-spacing:.04em; margin-bottom:.15rem;
      }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color:#91a8bf; line-height:1.45;
      }
      /* Premium dark selectors: remove the default white input surfaces. */
      [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background:linear-gradient(145deg,#152538,#101c2b) !important;
        border:1px solid #30465e !important;
        border-radius:10px !important;
        min-height:44px;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.025);
      }
      [data-testid="stSidebar"] [data-baseweb="select"] span,
      [data-testid="stSidebar"] [data-baseweb="select"] input {
        color:#edf5ff !important;
      }
      [data-testid="stSidebar"] [data-baseweb="select"] svg { fill:#72d6e7 !important; }
      [data-testid="stSidebar"] [data-testid="stRadio"] > label {
        color:#8fa7bf !important;
        font:600 .66rem 'DM Mono',monospace;
        letter-spacing:.13em;
        margin-bottom:.45rem;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap:5px;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        background:rgba(18,31,46,.62);
        border:1px solid transparent;
        border-radius:9px;
        padding:9px 11px;
        margin:0;
        transition:background .15s ease,border-color .15s ease,transform .15s ease;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background:#172a3d;
        border-color:#35516b;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
        background:linear-gradient(100deg,rgba(35,111,139,.35),rgba(20,44,65,.92));
        border-color:#3d8198;
        box-shadow:inset 3px 0 0 #58cde0,0 4px 14px rgba(0,0,0,.12);
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label p {
        color:#dce9f5;
        font-weight:600;
        font-size:.84rem;
      }
      [data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background:#62d2e4 !important;
        border:2px solid #e8fbff !important;
        box-shadow:0 0 0 4px rgba(82,199,223,.15);
      }
      [data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stTickBar"] {
        color:#91a8bf !important;
      }
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color:#849bb2;
        font-size:.72rem;
      }
      [data-testid="stSidebar"] hr {
        margin:.9rem 0 1rem 0;
        border-color:#26394e !important;
      }
      .sidebar-brand {
        padding:15px 14px 14px;
        border:1px solid #29445c;
        border-radius:13px;
        background:linear-gradient(135deg,rgba(27,65,89,.72),rgba(14,25,39,.92));
        box-shadow:0 12px 28px rgba(0,0,0,.16);
        margin-bottom:8px;
      }
      .sidebar-brand-mark {
        display:flex; align-items:center; gap:9px;
        color:#f0f7ff; font-weight:800; letter-spacing:.04em;
        font-size:1rem;
      }
      .sidebar-brand-icon {
        display:inline-flex; align-items:center; justify-content:center;
        width:27px; height:27px; border-radius:8px;
        background:rgba(82,199,223,.14); border:1px solid #3d8198;
        color:#71d9e9; font-size:1.05rem;
      }
      .sidebar-brand-sub {
        margin-top:7px; color:#9bb0c5; font: .62rem 'DM Mono',monospace;
        letter-spacing:.13em;
      }
      .sidebar-section-label {
        color:#69cfe0; font:500 .62rem 'DM Mono',monospace;
        letter-spacing:.15em; margin:4px 0 8px;
      }
      .sidebar-selection {
        padding:9px 11px; border-radius:9px;
        border:1px solid #2a435a; background:rgba(18,34,50,.68);
        color:#a9bdd0; font-size:.72rem; margin:7px 0 11px;
      }
      .sidebar-selection b { color:#f0f6fc; }
      .sidebar-footer {
        border-top:1px solid #26394e; padding-top:12px; margin-top:12px;
        color:#8fa5ba; font:.63rem 'DM Mono',monospace;
        letter-spacing:.04em; line-height:1.6;
      }
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
    response = httpx.get(f"{API_BASE_URL}/options", timeout=60.0)
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


@st.cache_data(ttl=60, max_entries=256, show_spinner=False)
def load_inventory(
    store_id: str, item_id: str, service_level: float,
    lead_time: int, current_inventory: float, review_period: int = 7,
) -> dict[str, Any]:
    response = httpx.post(
        f"{API_BASE_URL}/inventory",
        json={
            "store_id": store_id, "item_id": item_id,
            "service_level": service_level, "lead_time_days": lead_time,
            "current_inventory": current_inventory,
            "review_period_days": review_period,
        },
        timeout=httpx.Timeout(90.0, connect=15.0),
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, max_entries=128, show_spinner=False)
def load_eda(store_id: str, item_id: str) -> dict[str, Any]:
    response = httpx.get(
        f"{API_BASE_URL}/eda",
        params={"store_id": store_id, "item_id": item_id},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=600, max_entries=1, show_spinner=False)
def load_network() -> dict[str, Any]:
    response = httpx.get(f"{API_BASE_URL}/network", timeout=60.0)
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
        timeout=60.0,
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
        # Reserve space above the plot so legends are not clipped on mobile.
        margin=dict(l=22, r=24, t=76 if legend else 32, b=28),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#e5edf7", size=12),
        legend=dict(
            visible=True,
            orientation="h",
            yanchor="top", y=1.18,
            xanchor="left", x=0,
            font=dict(family="Manrope, sans-serif", color="#f2f6fc", size=12),
            bgcolor="rgba(13,22,34,.96)",
            bordercolor="#40566d", borderwidth=1,
            itemsizing="constant",
            itemwidth=80,
            tracegroupgap=8,
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
    fig.add_vline(x=history["date"].max(), line_dash="dot",
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
                     service_level: float, lead_time: int,
                     available_pairs: pd.DataFrame) -> None:
    st.markdown('<div class="eyebrow">DECISION SCIENCE / PERIODIC REVIEW</div>', unsafe_allow_html=True)
    st.header("Inventory control tower")
    st.caption("Periodic-review replenishment uses a 365-day demand window and a 7-day review cycle. On-hand stock is used as the inventory position.")
    selector_store_col, selector_item_col = st.columns(2)
    available_stores = sorted(available_pairs["store_id"].astype(str).unique().tolist())
    selected_store = selector_store_col.selectbox(
        "Select store", available_stores,
        index=available_stores.index(store) if store in available_stores else 0,
        key="inventory_store_selector",
    )
    available_items = sorted(
        available_pairs.loc[
            available_pairs["store_id"].astype(str) == selected_store, "item_id"
        ].astype(str).unique().tolist()
    )
    selected_item = selector_item_col.selectbox(
        "Select SKU / product", available_items,
        index=available_items.index(item) if item in available_items else 0,
        key=f"inventory_item_selector_{selected_store}",
    )
    store, item = selected_store, selected_item

    state_names = {
        "CA": "California",
        "TX": "Texas",
        "WI": "Wisconsin",
    }
    state_code = store.split("_", 1)[0] if "_" in store else store
    state_name = state_names.get(state_code, "State not mapped")
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 16px 0;">'
        f'<div style="flex:1;min-width:180px;padding:12px 14px;border:1px solid #2a4056;'
        f'border-radius:10px;background:#101b29;">'
        f'<div class="small-mono">SELECTED STORE / STATE</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:#e7eef7">{store} · {state_name}</div>'
        f'<div style="font-size:.72rem;color:#91a4b8">M5 dataset identifier · physical address not supplied</div></div>'
        f'<div style="flex:1;min-width:180px;padding:12px 14px;border:1px solid #2a4056;'
        f'border-radius:10px;background:#101b29;">'
        f'<div class="small-mono">SELECTED SKU / ITEM</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:#e7eef7">{item}</div>'
        f'<div style="font-size:.72rem;color:#91a4b8">M5 item identifier</div></div></div>',
        unsafe_allow_html=True,
    )
    # Geographic context for the selected M5 store. Store location is only
    # known at state level; the hub pins are explicitly synthetic scenarios.
    try:
        network_payload = load_network()
        network_states = pd.DataFrame(network_payload.get("states", []))
        network_centres = pd.DataFrame(network_payload.get("distribution_centers", []))
        if not network_states.empty:
            network_states["is_selected_state"] = (
                network_states["state_code"].astype(str) == state_code
            )
            store_rows = pd.DataFrame(network_payload.get("stores", []))
            selected_store_rows = store_rows.loc[
                store_rows["store_id"].astype(str) == store
            ] if not store_rows.empty else pd.DataFrame()
            store_demand = (
                float(selected_store_rows["total_demand"].sum())
                if not selected_store_rows.empty else float("nan")
            )
            state_row = network_states.loc[network_states["is_selected_state"]]
            state_demand = (
                float(state_row["total_demand"].iloc[0])
                if not state_row.empty else float("nan")
            )
            selected_item_demand = (
                float(pd.to_numeric(history["demand"], errors="coerce").fillna(0).sum())
                if "demand" in history.columns else float("nan")
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("State sales volume", money(state_demand), "units")
            m2.metric("Selected store sales", money(store_demand), "units")
            m3.metric("Selected SKU sales", money(selected_item_demand), "units")
            m4.metric("Stores in state", int(state_row["store_count"].iloc[0]) if not state_row.empty else 0)

            card_title(
                "Demand heatmap by state",
                f"Historical units sold · selected store {store} ({state_name}) is highlighted in the summary.",
            )
            geo_fig = px.choropleth(
                network_states,
                locations="state_code",
                locationmode="USA-states",
                color="total_demand",
                hover_name="state_name",
                hover_data={
                    "state_code": True,
                    "store_count": True,
                    "series_count": True,
                    "total_demand": ":,.0f",
                    "is_selected_state": True,
                },
                color_continuous_scale=["#142638", "#267a91", "#65d1df"],
                scope="usa",
                labels={
                    "total_demand": "Historical units sold",
                    "store_count": "Stores",
                    "series_count": "Store-item series",
                    "is_selected_state": "Selected state",
                },
            )
            if not network_centres.empty:
                geo_fig.add_trace(go.Scattergeo(
                    lon=network_centres["longitude"],
                    lat=network_centres["latitude"],
                    text=network_centres["distribution_center_id"],
                    mode="markers",
                    name="Synthetic DC anchors",
                    marker=dict(size=9, color="#f0b66b", symbol="diamond"),
                    hovertemplate="%{text}<br>Synthetic scenario location<extra></extra>",
                ))
            geo_fig.update_geos(
                showcountries=True, showland=True, landcolor="#0d1723",
                subunitcolor="#40566b", bgcolor="rgba(0,0,0,0)",
            )
            geo_fig.update_layout(
                template="plotly_dark", height=390,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Manrope, sans-serif", color="#f2f6fc", size=12),
                geo=dict(bgcolor="rgba(0,0,0,0)"),
                legend=dict(
                    visible=True, orientation="h",
                    yanchor="top", y=1.12, xanchor="left", x=0,
                    font=dict(color="#f2f6fc", size=12),
                    bgcolor="rgba(13,22,34,.96)",
                    bordercolor="#40566d", borderwidth=1,
                ),
                coloraxis_colorbar=dict(
                    title=dict(text="Units sold", font=dict(color="#f2f6fc", size=12)),
                    tickfont=dict(color="#e5edf7", size=11),
                    outlinecolor="#40566d",
                ),
            )
            st.plotly_chart(geo_fig, use_container_width=True, config=PLOT_CONFIG)
            st.caption("Color intensity represents historical units sold, not transaction counts. State shading is aggregated across the selected M5 sample; diamond markers are synthetic planning anchors.")

            if not store_rows.empty:
                card_title("Store-level sales volume", "Ranked M5 stores in the selected sample; select a store above to inspect its SKU.")
                store_rank = store_rows.sort_values("total_demand", ascending=False).copy()
                store_rank["selected"] = store_rank["store_id"].astype(str) == store
                rank_fig = px.bar(
                    store_rank,
                    x="store_id",
                    y="total_demand",
                    color="selected",
                    hover_data=["state_name", "series_count", "item_count", "average_daily_demand"],
                    color_discrete_map={True: "#f0b66b", False: "#55c8df"},
                    labels={"store_id": "M5 store", "total_demand": "Historical units sold", "selected": "Selected store"},
                )
                rank_fig.update_layout(
                    showlegend=True, xaxis_title="Store", yaxis_title="Historical units sold",
                    legend=dict(
                        title=None, orientation="h", yanchor="bottom", y=1.02,
                        xanchor="left", x=0, font=dict(color="#f2f6fc", size=12),
                        bgcolor="rgba(13,22,34,.96)", bordercolor="#40566d", borderwidth=1,
                    ),
                )
                st.caption("Legend: amber = selected store · cyan = other stores")
                st.plotly_chart(plot_layout(rank_fig, 330), use_container_width=True, config=PLOT_CONFIG)
    except Exception as geo_exc:
        st.warning(f"Geographic context is temporarily unavailable: {geo_exc}")

    current = st.number_input(
        "On-hand inventory (units)",
        min_value=0.0,
        value=20.0,
        step=1.0,
        key=f"inventory_on_hand_{store}_{item}",
        help="The live stock quantity used by the replenishment decision and gauge.",
    )
    try:
        with st.spinner("Calculating replenishment policy…"):
            result = load_inventory(store, item, service_level, lead_time, current, 7)
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
    c3.metric("Protection-period demand", money(result["mean_daily_demand"] * result["protection_period_days"]), f'{result["protection_period_days"]} days (L + R)')
    c4.metric("Suggested order", money(result["order_quantity"]), "units")

    left, right = st.columns([1, 1.35])
    with left:
        card_title("Stock position gauge")
        gauge_value = float(current)
        gauge_max = max(reorder * 1.5, gauge_value * 1.2, 1)
        # Keep the numeric readout in Streamlit rather than inside Plotly.
        # Plotly can preserve the old Indicator number in some mobile browser
        # update paths even while the gauge needle receives the new value.
        st.metric("Current stock", f"{gauge_value:,.1f} units")
        fig = go.Figure(go.Indicator(
            mode="gauge",
            value=gauge_value,
            gauge={
                "axis": {"range": [0, gauge_max]},
                "bar": {"color": status_color},
                "bgcolor": "#152233",
                "bordercolor": "#304459",
                "steps": [
                    {"range": [0, reorder], "color": "rgba(255,116,124,.16)"},
                    {"range": [reorder, gauge_max], "color": "rgba(87,214,141,.12)"},
                ],
                "threshold": {"line": {"color": "#f0b66b", "width": 3}, "value": reorder},
            },
        ))
        fig.update_layout(uirevision=f"stock-gauge-{store}-{item}-{gauge_value:.2f}-{reorder:.2f}")
        st.plotly_chart(
            plot_layout(fig, 280, legend=False),
            use_container_width=True,
            config=PLOT_CONFIG,
            key=f"stock_gauge_{store}_{item}_{gauge_value:.2f}_{reorder:.2f}",
        )
        st.caption(f"Reorder threshold: **{reorder:,.1f} units** · Gauge needle represents current stock.")
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
    protection_days = int(result.get("protection_period_days", lead_time + 7))
    safety = std * np.sqrt(max(protection_days, 1)) * z_values
    sensitivity = pd.DataFrame({
        "Service level": levels,
        "Safety stock": safety,
        "Reorder point": mean * protection_days + safety,
    })
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sensitivity["Service level"], y=sensitivity["Reorder point"],
                             mode="lines+markers", name="Reorder point",
                             line=dict(color="#56c9df", width=2.5)))
    fig.add_trace(go.Scatter(x=sensitivity["Service level"], y=sensitivity["Safety stock"],
                             mode="lines+markers", name="Safety stock",
                             line=dict(color="#b58ae8", width=2)))
    st.plotly_chart(plot_layout(fig, 300), use_container_width=True, config=PLOT_CONFIG)
    st.caption("Sensitivity curve uses the same protection period (lead time + 7-day review cycle) and a normal-demand approximation; it is not a fresh inventory simulation. Open purchase orders are not included in the live inventory position.")
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



def render_eda(store: str, item: str) -> None:
    st.markdown('<div class="eyebrow">STATISTICAL EXPLORATION / FULL HISTORY</div>', unsafe_allow_html=True)
    st.header("Exploratory data analysis")
    st.markdown(
        '<div class="hero-sub">Full historical demand profile · distribution · temporal structure · intermittency · dependence</div>',
        unsafe_allow_html=True,
    )
    try:
        with st.spinner("Computing full-history descriptive statistics…"):
            payload = load_eda(store, item)
    except Exception as exc:
        st.error(f"EDA service unavailable: {exc}")
        return

    stats = payload.get("stats", {})
    daily = pd.DataFrame(payload.get("daily", []))
    if daily.empty:
        st.warning("No historical observations were returned for this series.")
        return
    daily["date"] = pd.to_datetime(daily["date"])
    daily["demand"] = pd.to_numeric(daily["demand"], errors="coerce").fillna(0.0)

    st.caption(
        f"Series {store} × {item} · {stats.get('observations', len(daily)):,} observations · "
        f"{stats.get('start_date', '—')} to {stats.get('end_date', '—')}"
    )
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total demand", money(stats.get("total_demand")), "units")
    k2.metric("Daily mean", money(stats.get("mean")), "units / day")
    k3.metric("Median", money(stats.get("median")), "units / day")
    k4.metric("Demand std", money(stats.get("std")), "units")
    k5.metric("Zero-demand days", pct(stats.get("zero_demand_rate")), "intermittency")

    k6, k7, k8, k9, k10 = st.columns(5)
    k6.metric("Coefficient of variation", money(stats.get("coefficient_of_variation"),))
    k7.metric("Skewness", money(stats.get("skewness")))
    k8.metric("90th percentile", money(stats.get("q90")))
    k9.metric("Maximum demand", money(stats.get("maximum")))
    k10.metric("Non-zero mean", money(stats.get("nonzero_mean")))

    st.divider()
    left, right = st.columns([1.6, 1])
    with left:
        card_title("Long-run demand trend", "Daily demand and 28-day rolling mean across the full history.")
        trend = daily.copy()
        trend["28-day mean"] = trend["demand"].rolling(28, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["date"], y=trend["demand"], name="Daily demand",
                                 mode="lines", line=dict(color="#56c9df", width=1)))
        fig.add_trace(go.Scatter(x=trend["date"], y=trend["28-day mean"], name="28-day mean",
                                 mode="lines", line=dict(color="#f0b66b", width=2.5)))
        st.plotly_chart(plot_layout(fig, 350), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Demand distribution", "Histogram based on all daily observations.")
        hist = payload.get("histogram", {})
        edges = hist.get("edges", [])
        counts = hist.get("counts", [])
        if len(edges) == len(counts) + 1:
            centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(counts))]
            widths = [edges[i + 1] - edges[i] for i in range(len(counts))]
            fig = go.Figure(go.Bar(x=centers, y=counts, width=widths,
                                   marker_color="#58cce1", opacity=.85))
            fig.update_layout(xaxis_title="Daily demand", yaxis_title="Frequency")
            st.plotly_chart(plot_layout(fig, 350, legend=False), use_container_width=True, config=PLOT_CONFIG)

    left, right = st.columns(2)
    with left:
        card_title("Monthly demand and volatility", "Monthly total demand and within-month standard deviation.")
        monthly = pd.DataFrame(payload.get("monthly", []))
        if not monthly.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly["month"], y=monthly["sum"], name="Total demand",
                                 marker_color="#56c9df"))
            fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["std"], name="Daily std",
                                     yaxis="y2", line=dict(color="#f0b66b", width=2)))
            fig.update_layout(yaxis=dict(title="Units"), yaxis2=dict(title="Daily std", overlaying="y", side="right"))
            st.plotly_chart(plot_layout(fig, 330), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Day-of-week seasonality", "Mean, median and dispersion by weekday.")
        weekday = pd.DataFrame(payload.get("weekday", []))
        if not weekday.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=weekday["weekday"], y=weekday["mean"], name="Mean",
                                 marker_color="#56c9df"))
            fig.add_trace(go.Scatter(x=weekday["weekday"], y=weekday["median"], name="Median",
                                     mode="lines+markers", line=dict(color="#f0b66b", width=2)))
            st.plotly_chart(plot_layout(fig, 330), use_container_width=True, config=PLOT_CONFIG)

    left, right = st.columns(2)
    with left:
        card_title("Month-of-year seasonal pattern", "Average demand by calendar month, pooled across years.")
        months = pd.DataFrame(payload.get("month_of_year", []))
        if not months.empty:
            fig = px.bar(months, x="month_name", y="demand",
                         color="demand", color_continuous_scale=["#17384b", "#58cce1"])
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Month", yaxis_title="Mean daily demand")
            st.plotly_chart(plot_layout(fig, 300, legend=False), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("Autocorrelation diagnostics", "Pearson autocorrelation at selected daily lags.")
        lags = ["1 day", "7 days", "28 days"]
        values = [stats.get("lag1_autocorrelation"), stats.get("lag7_autocorrelation"), stats.get("lag28_autocorrelation")]
        acf = pd.DataFrame({"Lag": lags, "Autocorrelation": [v if v is not None else 0 for v in values]})
        fig = px.bar(acf, x="Lag", y="Autocorrelation",
                     color="Autocorrelation", color_continuous_scale=["#b58ae8", "#56c9df"])
        fig.add_hline(y=0, line_color="#8fa1b5", line_width=1)
        fig.update_layout(coloraxis_showscale=False, yaxis_range=[-1, 1])
        st.plotly_chart(plot_layout(fig, 300, legend=False), use_container_width=True, config=PLOT_CONFIG)

    st.subheader("Statistical profile")
    quantile_rows = [
        {"Statistic": label, "Demand": stats.get(key)}
        for label, key in [
            ("Minimum", "minimum"), ("25th percentile", "q25"),
            ("Median / 50th percentile", "q50"), ("75th percentile", "q75"),
            ("90th percentile", "q90"), ("95th percentile", "q95"),
            ("99th percentile", "q99"), ("Maximum", "maximum"),
            ("Variance", "variance"), ("Kurtosis", "kurtosis"),
            ("Price-demand correlation", "price_demand_correlation"),
        ]
    ]
    st.dataframe(pd.DataFrame(quantile_rows), use_container_width=True, hide_index=True)
    with st.expander("Inspect full daily history"):
        st.dataframe(daily, use_container_width=True, hide_index=True)
    st.caption("Autocorrelation is descriptive, not causal. Price correlation is unadjusted and should not be interpreted as a price elasticity estimate.")



def render_network_intelligence() -> None:
    st.markdown('<div class="eyebrow">GEOSPATIAL ANALYTICS / NETWORK DESIGN</div>', unsafe_allow_html=True)
    st.header("Network intelligence")
    st.caption("NETWORK INTELLIGENCE · BUILD 2026.11.11 · STATE-LEVEL OBSERVED DATA + SYNTHETIC HUB SCENARIO")
    st.markdown(
        '<div class="hero-sub">Observed M5 demand aggregated by state, with a separate synthetic distribution-centre scenario layer.</div>',
        unsafe_allow_html=True,
    )
    try:
        with st.spinner("Loading state-level network aggregates…"):
            payload = load_network()
    except Exception as exc:
        st.error(f"Network analytics unavailable: {exc}")
        st.info("Confirm that the latest FastAPI deployment is live and the processed forecast feature artifact is present.")
        return

    states = pd.DataFrame(payload.get("states", []))
    stores = pd.DataFrame(payload.get("stores", []))
    centres = pd.DataFrame(payload.get("distribution_centers", []))
    metadata = payload.get("metadata", {})
    if states.empty:
        st.warning("No state-level store data is available.")
        return

    st.markdown(
        '<div style="padding:11px 14px;border:1px solid #7c633a;border-radius:10px;'
        'background:rgba(87,64,28,.18);color:#e8c58e;font-size:.78rem;margin:8px 0 14px 0;">'
        '<b>Geography policy:</b> store performance is shown at state level only. '
        'Distribution-centre markers are synthetic scenario anchors, not real warehouses. '
        'No real road distance or route is implied.</div>',
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("M5 states represented", f"{len(states):,}")
    k2.metric("Stores in selected sample", f"{int(states['store_count'].sum()):,}")
    k3.metric("Store-item series", f"{int(states['series_count'].sum()):,}")
    k4.metric("Historical demand", money(states["total_demand"].sum()), "units")

    card_title("State-level demand intensity", "Interactive US state map · demand aggregated by state; no precise store pins.")
    fig = px.choropleth(
        states,
        locations="state_code",
        locationmode="USA-states",
        color="total_demand",
        hover_name="state_name",
        hover_data={
            "state_code": True,
            "store_count": True,
            "series_count": True,
            "item_count": True,
            "total_demand": ":,.0f",
            "average_daily_demand": ":,.1f",
        },
        color_continuous_scale=["#142b3c", "#267a91", "#65d1df"],
        scope="usa",
        labels={
            "total_demand": "Historical demand",
            "store_count": "Stores",
            "series_count": "Series",
            "item_count": "Items",
            "average_daily_demand": "Avg daily demand",
        },
    )
    if not centres.empty:
        fig.add_trace(go.Scattergeo(
            lon=centres["longitude"],
            lat=centres["latitude"],
            text=centres["distribution_center_id"],
            customdata=centres[["city_label", "state_name"]],
            mode="markers+text",
            textposition="top center",
            name="Synthetic DC scenario anchors",
            marker=dict(size=11, color="#f0b66b", symbol="diamond",
                        line=dict(color="#fff0d6", width=1)),
            hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>%{customdata[1]}<br>Synthetic only<extra></extra>",
        ))
    fig.update_geos(
        showcountries=True,
        countrycolor="#40566b",
        showland=True,
        landcolor="#0d1723",
        showlakes=True,
        lakecolor="#0b1520",
        bgcolor="rgba(0,0,0,0)",
        subunitcolor="#33485c",
    )
    fig.update_layout(
        template="plotly_dark",
        height=540,
        margin=dict(l=0, r=0, t=18, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        coloraxis_colorbar=dict(title="Demand", tickformat=",.2s"),
        legend=dict(orientation="h", y=-.04, x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    left, right = st.columns([1.15, 1])
    with left:
        card_title("State performance", "Ranked historical demand across represented states.")
        state_view = states.sort_values("total_demand", ascending=False).copy()
        fig = px.bar(
            state_view,
            x="state_code",
            y="total_demand",
            color="total_demand",
            color_continuous_scale=["#18384c", "#58cce1"],
            hover_data=["store_count", "series_count", "item_count"],
        )
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_title="State",
            yaxis_title="Historical demand",
        )
        st.plotly_chart(plot_layout(fig, 330, legend=False), use_container_width=True, config=PLOT_CONFIG)
    with right:
        card_title("State summary", "Store and SKU coverage in the selected M5 sample.")
        st.dataframe(
            state_view[["state_name", "store_count", "series_count", "total_demand"]].rename(
                columns={
                    "state_name": "State",
                    "store_count": "Stores",
                    "series_count": "Series",
                    "total_demand": "Demand",
                }
            ).round(1),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Synthetic distribution-centre scenario")
    st.caption("Each sample store is assigned to a synthetic scenario hub by state code. These assignments are illustrative, not observed retailer logistics.")
    if not centres.empty:
        centre_view = centres[["distribution_center_id", "city_label", "state_name"]].merge(
            stores.groupby(["distribution_center_id", "state_name"], as_index=False).agg(
                assigned_stores=("store_id", "nunique"),
                assigned_series=("series_count", "sum"),
                historical_demand=("total_demand", "sum"),
            ),
            on=["distribution_center_id", "state_name"],
            how="left",
        ).fillna(0)
        columns = st.columns(min(3, len(centre_view)))
        for col, (_, row) in zip(columns, centre_view.iterrows()):
            with col:
                st.metric(
                    str(row["distribution_center_id"]),
                    f"{int(row['assigned_stores'])} stores",
                    f"{int(row['assigned_series'])} series",
                )
                st.caption(f"{row['city_label']} · synthetic")
        store_view = stores[
            [
                "store_id", "state_name", "distribution_center_id",
                "assignment_type", "series_count", "item_count",
                "average_daily_demand", "total_demand",
            ]
        ].sort_values(["state_name", "store_id"])
        st.dataframe(
            store_view.rename(columns={
                "store_id": "M5 store",
                "state_name": "State",
                "distribution_center_id": "Scenario hub",
                "assignment_type": "Assignment basis",
                "series_count": "Series",
                "item_count": "Items",
                "average_daily_demand": "Avg daily demand",
                "total_demand": "Historical demand",
            }).round(1),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Geography and data provenance"):
        st.json(metadata)
        st.markdown(
            "State-level geography is approximate. Distribution-centre points are generated scenario anchors "
            "near representative cities. They are not real facilities, and this page does not estimate "
            "road distance, freight cost, or real service territories."
        )


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
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-mark"><span class="sidebar-brand-icon">◇</span> RETAIL / INTEL</div>'
        '<div class="sidebar-brand-sub">DEMAND · FORECAST · INVENTORY</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section-label">DATA SCOPE</div>', unsafe_allow_html=True)
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
    st.markdown(
        f'<div class="sidebar-selection">ACTIVE SERIES<br><b>{store}</b> <span style="color:#66839c">/</span> <b>{item}</b></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section-label">WORKSPACES</div>', unsafe_allow_html=True)
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Full EDA", "Demand Forecast", "Inventory Control", "Network Intelligence", "Business Impact", "Scenario Studio"],
        label_visibility="collapsed",
        key="workspace_navigation_v2",
    )
    service_level = st.slider("Target service level", .80, .99, .90, .01, format="%.2f")
    lead_time = st.slider("Supplier lead time · days", 1, 30, 7)
    st.markdown('<div class="sidebar-section-label">SYSTEM STATUS</div>', unsafe_allow_html=True)
    st.markdown('<span class="status-pill">● API CONNECTED</span>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sidebar-footer">LIVE DATA CONNECTION<br>{API_BASE_URL}</div>',
        unsafe_allow_html=True,
    )


# ------------------------------ MAIN VIEW ------------------------------
st.caption(f"Active workspace: {page} · Dashboard build 2026.11.11.2")
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
elif page == "Full EDA":
    render_eda(store, item)
elif page == "Demand Forecast":
    render_forecast(history, store, item)
elif page == "Inventory Control":
    render_inventory(history, store, item, service_level, lead_time, pairs)
elif page == "Network Intelligence":
    render_network_intelligence()
elif page == "Business Impact":
    render_business()
elif page == "Scenario Studio":
    render_scenario(store, item, service_level, lead_time)
else:
    st.error(f"Unknown workspace selected: {page}")

st.markdown("---")
st.markdown(
    f'<span class="small-mono">DATA WINDOW: {history["date"].min().date()} → {history["date"].max().date()}'
    f' &nbsp; · &nbsp; SERIES OBSERVATIONS: {len(history)}'
    f' &nbsp; · &nbsp; API: {API_BASE_URL}</span>',
    unsafe_allow_html=True,
)
