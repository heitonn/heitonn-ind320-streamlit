import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# imports from utils
from utils.constants import city_data_df
from utils.weather_data_fetcher import get_weather_data
from utils.ui_helpers import choose_price_area

# page title and header
st.set_page_config(page_title="Weather visualizer", layout="wide")
st.header("Visualizing weather data")
st.write("Select a column and a month range to visualize the data. Use 'All columns' to see everything.")

# Reading data  
chosen_area, row = choose_price_area() # function in utils/ui_helpers.py

# Fetch weather data
df = get_weather_data(row["Latitude"], row["Longitude"], year=2021) #  function in utils/weather_data_fetcher.py

# Mapping column names to more user-friendly labels
column_names = {"temperature_2m": "Temperature (°C)",
                "precipitation": "Precipitation (mm)",
                "wind_speed_10m": "Wind Speed (m/s)",  
                "wind_gusts_10m": "Wind Gusts (m/s)",  
                "wind_direction_10m": "Wind Direction (°)"}
df.columns = [column_names.get(col, col) for col in df.columns]

# Creating dropdown for column selection
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
ax.set_ylabel(f"{selected_col}")  # Use y_labels for y-axis
ax.legend(loc="best")

st.pyplot(fig)