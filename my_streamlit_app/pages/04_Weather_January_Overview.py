import streamlit as st
import pandas as pd
from utils.constants import city_data_df
from utils.weather_data_fetcher import get_weather_data
from utils.ui_helpers import choose_price_area

st.set_page_config(page_title="January Weather", layout="wide")
st.header("Weatherdata January 2021 Overview")


# area selection
# radio buttens with area (price and city)
chosen_area, row = choose_price_area()
chosen_area = st.session_state.get("chosen_area")

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
