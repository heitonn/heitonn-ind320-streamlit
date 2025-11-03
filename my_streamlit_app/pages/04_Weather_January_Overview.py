import streamlit as st
import pandas as pd
from utils.constants import city_data_df
from utils.data_fetcher import get_weather_data

st.set_page_config(page_title="January Weather", layout="wide")
st.header("Weatherdata January 2021 Overview")

# --- AREA SELECTION ---
available_areas = city_data_df["PriceArea"].tolist()
labels = [
    f"{area} – {city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]}"
    for area in available_areas
]
label_to_area = {label: area for label, area in zip(labels, available_areas)}

# default
chosen_area = st.session_state.get("chosen_area", available_areas[0])
default_label = next((lbl for lbl, area in label_to_area.items() if area == chosen_area), labels[0])

# horisontale radioknapper
selected_label = st.radio(
    "Select price area:",
    labels,
    index=labels.index(default_label),
    horizontal=True
)
chosen_area = label_to_area[selected_label]
st.session_state["chosen_area"] = chosen_area

# hent data (try/except for sikkerhet)
filtered_rows = city_data_df[city_data_df["PriceArea"] == chosen_area]
if len(filtered_rows) == 0:
    st.error(f"No data found for {chosen_area}")
else:
    row = filtered_rows.iloc[0]
    df = get_weather_data(row["Latitude"], row["Longitude"], year=2021)

    # --- FILTER JANUARY ---
    january = df.loc["2021-01"]

    # --- CREATE TABLE ---
    january_table = pd.DataFrame({
        "Temperature (°C)": [january["temperature_2m"].values],
        "Precipitation (mm)": [january["precipitation"].values],
        "Wind speed (m/s)": [january["wind_speed_10m"].values],
        "Wind gusts (m/s)": [january["wind_gusts_10m"].values],
        "Wind direction (°)": [january["wind_direction_10m"].values],
    })

    # --- CLEAN UP ---
    january_table = january_table.T.reset_index()
    january_table.columns = ["Variable", "Values"]

    # --- DISPLAY ---
    st.dataframe(
        january_table,
        column_config={
            "Values": st.column_config.LineChartColumn("January"),
        },
        hide_index=True,
    )
