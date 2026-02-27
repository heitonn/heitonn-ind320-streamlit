import os
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

from utils.constants import city_data_df
from utils.load_energy_data import load_energy_data, load_consumption_data


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Energy Map", layout="wide", page_icon="🗺️")
st.title("🗺️ Energy Map")
st.caption("Klikk på et prisområde i kartet for å velge område. Se statistikk til høyre.")


# -----------------------------
# Cached GeoJSON
# -----------------------------
@st.cache_data(show_spinner=False)
def load_geojson() -> dict:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    geojson_path = os.path.join(base_dir, "assets", "file.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Cached aggregation
# -----------------------------
@st.cache_data(show_spinner=False)
def load_dataset(data_type: str) -> pd.DataFrame:
    if data_type == "Production":
        return load_energy_data()
    return load_consumption_data()


@st.cache_data(show_spinner=False)
def compute_area_means(
    df: pd.DataFrame,
    data_type: str,
    group: str,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
) -> pd.DataFrame:
    df = df.copy()
    df["starttime"] = pd.to_datetime(df["starttime"])

    mask = (df["starttime"] >= start_ts) & (df["starttime"] <= end_ts)
    df = df.loc[mask]

    group_col = "productiongroup" if data_type == "Production" else "consumptiongroup"
    if group != "Total" and group_col in df.columns:
        df = df[df[group_col] == group]

    out = (
        df.groupby("area", as_index=False)["quantitykwh"]
        .mean()
        .rename(columns={"quantitykwh": "mean_kwh"})
    )
    return out


def safe_groups(df: pd.DataFrame, data_type: str) -> list[str]:
    if data_type == "Production":
        col = "productiongroup"
    else:
        col = "consumptiongroup"
    if col not in df.columns:
        return ["Total"]
    groups = sorted(df[col].dropna().unique().tolist())
    if "Total" not in groups:
        groups = ["Total"] + groups
    return groups


# -----------------------------
# Session defaults
# -----------------------------
if "chosen_area" not in st.session_state:
    st.session_state["chosen_area"] = "NO1"


# -----------------------------
# Controls
# -----------------------------
geojson_data = load_geojson()
areas = city_data_df["PriceArea"].drop_duplicates().tolist()

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    data_type = st.selectbox("Data", ["Production", "Consumption"], index=0)
with c2:
    df_all = load_dataset(data_type)
    group = st.selectbox("Group", safe_groups(df_all, data_type), index=0)
with c3:
    days = st.slider("Days back", 7, 180, 30, 7)

end_ts = pd.Timestamp(datetime.now())
start_ts = end_ts - pd.Timedelta(days=days)


# -----------------------------
# Layout: map left, stats right
# -----------------------------
col_map, col_stats = st.columns([2, 1], gap="large")

with col_map:
    # Build map values (mean per area)
    area_means_df = compute_area_means(
        df=df_all,
        data_type=data_type,
        group=group,
        start_ts=start_ts,
        end_ts=end_ts,
    )

    # Ensure all areas present
    map_df = (
        pd.DataFrame({"area": areas})
        .merge(area_means_df, on="area", how="left")
        .fillna({"mean_kwh": 0.0})
    )

    # GeoJSON uses "NO 1"
    map_df["area_display"] = map_df["area"].str.replace("NO", "NO ", regex=False)

    fig = px.choropleth_mapbox(
        map_df,
        geojson=geojson_data,
        locations="area_display",
        featureidkey="properties.ElSpotOmr",
        color="mean_kwh",
        hover_name="area",
        hover_data={"area_display": False, "mean_kwh": ":.0f"},
        mapbox_style="carto-positron",
        center={"lat": 65, "lon": 15},
        zoom=3.5,
        opacity=0.65,
        labels={"mean_kwh": "Mean kWh"},
    )

    # Make clicks/selects possible
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        clickmode="event+select",
    )

    st.markdown(f"**Selected area:** `{st.session_state['chosen_area']}`")

    # Capture clicks from Plotly
    events = plotly_events(
        fig,
        click_event=True,
        select_event=False,
        hover_event=False,
        override_height=520,
        key="plotly_map_events",
    )

    if events:
        # For choropleth_mapbox, Plotly event contains "location" matching locations column
        loc = events[0].get("location")
        if isinstance(loc, str):
            new_area = loc.replace(" ", "")  # "NO 1" -> "NO1"
            if new_area in areas and new_area != st.session_state["chosen_area"]:
                st.session_state["chosen_area"] = new_area
                st.rerun()

    # Optional manual fallback
    with st.expander("Velg område manuelt"):
        chosen = st.selectbox(
            "Price area",
            areas,
            index=areas.index(st.session_state["chosen_area"]),
            key="manual_area_select",
        )
        if chosen != st.session_state["chosen_area"]:
            st.session_state["chosen_area"] = chosen
            st.rerun()


with col_stats:
    chosen_area = st.session_state["chosen_area"]
    st.subheader("📌 Statistics")

    # Filter df for chosen area + time window (+ group if not Total)
    df = df_all.copy()
    df["starttime"] = pd.to_datetime(df["starttime"])
    df = df[(df["area"] == chosen_area) & (df["starttime"] >= start_ts) & (df["starttime"] <= end_ts)]

    group_col = "productiongroup" if data_type == "Production" else "consumptiongroup"
    if group != "Total" and group_col in df.columns:
        df = df[df[group_col] == group]

    if df.empty:
        st.warning("No data for selection.")
        st.stop()

    # Basic metrics
    mean_v = float(df["quantitykwh"].mean())
    sum_v = float(df["quantitykwh"].sum())
    max_v = float(df["quantitykwh"].max())

    m1, m2, m3 = st.columns(3)
    m1.metric("Mean", f"{mean_v:,.0f}")
    m2.metric("Sum", f"{sum_v:,.0f}")
    m3.metric("Max", f"{max_v:,.0f}")

    st.caption(f"Period: {start_ts.date()} → {end_ts.date()}")

    # Small time series (daily sum)
    st.markdown("#### Trend")
    series = (
        df.set_index("starttime")["quantitykwh"]
        .resample("D")
        .sum()
        .sort_index()
    )
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines"))
    fig_ts.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_ts, use_container_width=True)

    # Breakdown (if production and Total -> show groups)
    if data_type == "Production" and group == "Total" and "productiongroup" in df_all.columns:
        st.markdown("#### Breakdown (sum)")
        df_area = df_all.copy()
        df_area["starttime"] = pd.to_datetime(df_area["starttime"])
        df_area = df_area[(df_area["area"] == chosen_area) & (df_area["starttime"] >= start_ts) & (df_area["starttime"] <= end_ts)]
        grp = df_area.groupby("productiongroup")["quantitykwh"].sum().sort_values(ascending=False).head(8)
        st.dataframe(grp.reset_index().rename(columns={"quantitykwh": "sum_kwh"}), use_container_width=True, hide_index=True)