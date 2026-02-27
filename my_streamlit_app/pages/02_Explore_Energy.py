import streamlit as st
import pandas as pd
import plotly.express as px

from utils.ui_helpers import choose_price_area
from utils.load_energy_data import load_energy_data, load_consumption_data


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Energy Overview", layout="wide", page_icon="⚡")
st.title("⚡ Energy Overview")
st.markdown("Explore **daily** production (left) and **daily** consumption (right) for your selected region.")


# -----------------------------
# Load data (once)
# -----------------------------
prod_df = load_energy_data()
cons_df = load_consumption_data()

# Area selection
chosen_area, _ = choose_price_area(show_selector=True)

# Filter area once
prod_area = prod_df[prod_df["area"] == chosen_area].copy()
cons_area = cons_df[cons_df["area"] == chosen_area].copy()

# Ensure datetime
prod_area["starttime"] = pd.to_datetime(prod_area["starttime"])
cons_area["starttime"] = pd.to_datetime(cons_area["starttime"])


def _metrics_block(df: pd.DataFrame, label: str = "kWh"):
    if df.empty:
        st.info("No data for current filters.")
        return
    s = df["quantitykwh"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean", f"{s.mean():,.0f} {label}")
    c2.metric("Min", f"{s.min():,.0f} {label}")
    c3.metric("Max", f"{s.max():,.0f} {label}")


def _daily_sum_for_lineplot(
    df: pd.DataFrame,
    group_col: str | None,
    selected_groups: list[str] | None,
    chosen_year: int,
    chosen_month: str,
) -> pd.DataFrame:
    """Return a daily-summed DF with columns: date, quantitykwh (+ group col if exists)."""
    out = df.copy()

    # Apply filters
    if group_col and selected_groups:
        out = out[out[group_col].isin(selected_groups)]
    if "year" in out.columns:
        out = out[out["year"] == chosen_year]
    if "month" in out.columns:
        out = out[out["month"] == chosen_month]

    if out.empty:
        return out

    # Daily sum
    if group_col and group_col in out.columns:
        daily = (
            out.set_index("starttime")
               .groupby(group_col)["quantitykwh"]
               .resample("D")
               .sum()
               .reset_index()
               .rename(columns={"starttime": "date"})
        )
    else:
        daily = (
            out.set_index("starttime")["quantitykwh"]
               .resample("D")
               .sum()
               .reset_index()
               .rename(columns={"starttime": "date"})
        )

    return daily


# -----------------------------
# Shared Month/Year selectors
# -----------------------------
# Use production months/years as primary if available, else fallback to consumption
months = []
years = []

if "month" in prod_area.columns and "year" in prod_area.columns and not prod_area.empty:
    months = prod_area["month"].dropna().unique().tolist()
    years = sorted(prod_area["year"].dropna().unique().tolist())
elif "month" in cons_area.columns and "year" in cons_area.columns and not cons_area.empty:
    months = cons_area["month"].dropna().unique().tolist()
    years = sorted(cons_area["year"].dropna().unique().tolist())

# Safe defaults
if not months:
    st.error("Could not find month labels in data.")
    st.stop()
if not years:
    st.error("Could not find years in data.")
    st.stop()

st.subheader("Common filters")
f1, f2 = st.columns(2)
with f1:
    chosen_month = st.selectbox("Month", months, index=0, key="common_month")
with f2:
    chosen_year = st.selectbox("Year", years, index=len(years) - 1, key="common_year")

st.divider()


# -----------------------------
# Layout: Production (left) / Consumption (right)
# -----------------------------
col_prod, col_cons = st.columns(2, gap="large")

# =========================================================
# LEFT: PRODUCTION
# =========================================================
with col_prod:
    st.header("🔌 Production")

    group_col = "productiongroup" if "productiongroup" in prod_area.columns else None
    prod_groups = sorted(prod_area[group_col].dropna().unique().tolist()) if group_col else []

    st.subheader("Daily production over time")
    sel_prod_groups = st.pills(
        "Groups",
        options=prod_groups,
        selection_mode="multi",
        default=prod_groups[:1] if prod_groups else None,
        key="prod_groups_pills",
    )

    prod_daily = _daily_sum_for_lineplot(
        df=prod_area,
        group_col=group_col,
        selected_groups=sel_prod_groups,
        chosen_year=chosen_year,
        chosen_month=chosen_month,
    )

    if not prod_daily.empty:
        fig_prod_line = px.line(
            prod_daily,
            x="date",
            y="quantitykwh",
            color=group_col if group_col else None,
            markers=False,
            title=f"{chosen_area} – {chosen_month} {chosen_year} (daily sum)",
            labels={"date": "Date", "quantitykwh": "kWh/day", "productiongroup": "Group"},
        )
        fig_prod_line.update_layout(height=360, margin=dict(l=20, r=20, t=60, b=40), hovermode="x unified")
        st.plotly_chart(fig_prod_line, use_container_width=True)
    else:
        st.write("Ingen produksjonsdata for valgt kombinasjon.")

    st.divider()

    st.subheader("Total production per group (year)")
    prod_year_df = prod_area.copy()
    if "year" in prod_year_df.columns:
        prod_year_df = prod_year_df[prod_year_df["year"] == chosen_year]

    if not prod_year_df.empty and "productiongroup" in prod_year_df.columns:
        prod_group_sum = (
            prod_year_df.groupby("productiongroup", as_index=False)["quantitykwh"]
            .sum()
            .sort_values("quantitykwh", ascending=False)
        )
        fig_prod_pie = px.pie(
            prod_group_sum,
            values="quantitykwh",
            names="productiongroup",
            title=f"Total production by group in {chosen_area} ({chosen_year})",
            hole=0.35,
        )
        fig_prod_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Sum: %{value:,.0f} kWh<br>%{percent}<extra></extra>",
        )
        fig_prod_pie.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig_prod_pie, use_container_width=True)
    else:
        st.write("Ingen produksjonsdata for pie chart.")


# =========================================================
# RIGHT: CONSUMPTION
# =========================================================
with col_cons:
    st.header("🏠 Consumption")

    group_col = "consumptiongroup" if "consumptiongroup" in cons_area.columns else None
    cons_groups = sorted(cons_area[group_col].dropna().unique().tolist()) if group_col else []

    st.subheader("Daily consumption over time")
    sel_cons_groups = st.pills(
        "Groups",
        options=cons_groups,
        selection_mode="multi",
        default=cons_groups[:1] if cons_groups else None,
        key="cons_groups_pills",
    )

    cons_daily = _daily_sum_for_lineplot(
        df=cons_area,
        group_col=group_col,
        selected_groups=sel_cons_groups,
        chosen_year=chosen_year,
        chosen_month=chosen_month,
    )

    if not cons_daily.empty:
        fig_cons_line = px.line(
            cons_daily,
            x="date",
            y="quantitykwh",
            color=group_col if group_col else None,
            markers=False,
            title=f"{chosen_area} – {chosen_month} {chosen_year} (daily sum)",
            labels={"date": "Date", "quantitykwh": "kWh/day", "consumptiongroup": "Group"},
        )
        fig_cons_line.update_layout(height=360, margin=dict(l=20, r=20, t=60, b=40), hovermode="x unified")
        st.plotly_chart(fig_cons_line, use_container_width=True)
    else:
        st.write("Ingen konsumdata for valgt kombinasjon.")

    st.divider()

    st.subheader("Total consumption per group (year)")
    cons_year_df = cons_area.copy()
    if "year" in cons_year_df.columns:
        cons_year_df = cons_year_df[cons_year_df["year"] == chosen_year]

    if not cons_year_df.empty and group_col:
        cons_group_sum = (
            cons_year_df.groupby(group_col, as_index=False)["quantitykwh"]
            .sum()
            .sort_values("quantitykwh", ascending=False)
        )
        fig_cons_pie = px.pie(
            cons_group_sum,
            values="quantitykwh",
            names=group_col,
            title=f"Total consumption by group in {chosen_area} ({chosen_year})",
            hole=0.35,
        )
        fig_cons_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Sum: %{value:,.0f} kWh<br>%{percent}<extra></extra>",
        )
        fig_cons_pie.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig_cons_pie, use_container_width=True)
    else:
        st.write("Ingen konsumdata for pie chart.")


# -----------------------------
# Data source
# -----------------------------
with st.expander("Data source"):
    st.markdown(
        """
        The presented data on this page is collected from the
        [**Elhub** database](https://api.elhub.no/energy-data-api).

        The dataset contains hourly energy data across the five Norwegian price areas **NO1–NO5**.
        Values represent measured **energy in kWh per hour**.
        """
    )