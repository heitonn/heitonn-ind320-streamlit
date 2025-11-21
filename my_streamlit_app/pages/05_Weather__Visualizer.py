import streamlit as st
import pandas as pd
import plotly.express as px

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

# Year selection and column selection in columns
col1, col2 = st.columns(2)

with col1:
    year = st.selectbox("Select Year", [2021, 2022, 2023, 2024], index=0)

# Fetch weather data
df = get_weather_data(row["Latitude"], row["Longitude"], year=year) #  function in utils/weather_data_fetcher.py

# Mapping column names to more user-friendly labels
column_names = {"temperature_2m": "Temperature (°C)",
                "precipitation": "Precipitation (mm)",
                "wind_speed_10m": "Wind Speed (m/s)",  
                "wind_gusts_10m": "Wind Gusts (m/s)",  
                "wind_direction_10m": "Wind Direction (°)"}
df.columns = [column_names.get(col, col) for col in df.columns]

# Creating dropdown for column selection
options = list(df.columns) + ["All columns"]

with col2:
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

# Plotting with Plotly
if selected_col == "All columns":
    # Plot all columns
    fig = px.line(
        df_subset.reset_index(),
        x='time',
        y=df_subset.columns.tolist(),
        title="Weather data",
        labels={'value': 'Value', 'time': 'Time', 'variable': 'Variable'}
    )
else:
    # Plot selected column
    fig = px.line(
        df_subset.reset_index(),
        x='time',
        y=selected_col,
        title="Weather data",
        labels={selected_col: selected_col, 'time': 'Time'}
    )

fig.update_layout(
    xaxis_title="Time",
    yaxis_title=selected_col,
    height=500,
    margin=dict(l=40, r=40, t=60, b=40),
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)