import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from utils.constants import city_data_df
from utils.data_fetcher import get_weather_data


st.set_page_config(page_title="Weather visualizer", layout="wide")
st.header("Visualizing weather data")
st.write("Select a column and a month range to visualize the data. Use 'All columns' to see everything.")

# Reading data 
chosen_area = st.session_state.get("chosen_area", "NO5")
row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]
df = get_weather_data(row["Latitude"], row["Longitude"], year=2021)

# --- AREA SELECTION ---
# Hent valgt område fra session_state eller default til NO5
chosen_area = st.session_state.get("chosen_area", "NO5")
areas = [f"NO{i}" for i in range(1, 6)]

# Lag labels som viser både NOx og bynavn
labels = [f"{area} – {city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]}" for area in areas]

# Radio for å velge område
selected_label = st.radio("Select price area:", labels, index=areas.index(chosen_area), horizontal=True)

# Oppdater session_state
chosen_area = selected_label.split(" – ")[0]  # bare NOx
st.session_state["chosen_area"] = chosen_area

# Vis valgt område
st.write(f"**Currently selected area:** {selected_label}")
# Choosing column (or all columns)
options = list(df.columns) + ["All columns"]
selected_col = st.selectbox("Select column(s) to plot:", options)

# Sorting data per month 
months = sorted(df.index.to_period("M").unique().strftime("%Y-%m"))
# Selecting month slider
selected_months = st.select_slider(
    "Select months range:",
    options=months,
    value=(months[0], months[0])  # default = first month
)

# Filtering on chosen month
start, end = pd.Period(selected_months[0]), pd.Period(selected_months[1])
mask = (df.index.to_period("M") >= start) & (df.index.to_period("M") <= end)
df_subset = df.loc[mask]

# Plotting 
fig, ax = plt.subplots(figsize=(10,5))
if selected_col == "All columns":
    df_subset.plot(ax=ax)
else:
    df_subset[selected_col].plot(ax=ax)

ax.set_title("Weather data")
ax.set_xlabel("Time")
ax.set_ylabel("Value")
ax.legend(loc="best")

st.pyplot(fig)