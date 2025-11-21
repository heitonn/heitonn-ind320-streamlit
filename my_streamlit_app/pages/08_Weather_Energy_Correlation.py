import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Import utility functions
from utils.ui_helpers import choose_price_area
from utils.load_energy_data import load_energy_data_v2, load_consumption_data
from utils.weather_data_fetcher import get_weather_data
from utils.constants import city_data_df

st.set_page_config(page_title="Weather-Energy Correlation", layout="wide")
st.title("⚡🌤️ Weather-Energy Sliding Window Correlation")

st.markdown("""
This page shows the **sliding window correlation** between weather variables and energy production/consumption.
A sliding window correlation calculates correlation in moving time windows, revealing how the relationship changes over time.
""")

# Price area selector
chosen_area, city_info = choose_price_area(show_selector=True)

# Get city coordinates for this area
lat, lon = city_info['Latitude'], city_info['Longitude']
city_name = city_info['City']

st.markdown(f"**Selected area:** {chosen_area} ({city_name})")

# Year selector
col1, col2 = st.columns(2)
with col1:
    year = st.selectbox("Year", [2021, 2022, 2023, 2024], index=3)

# Define available variables
weather_variables = {
    "Temperature (°C)": "temperature_2m",
    "Precipitation (mm)": "precipitation",
    "Wind Speed (m/s)": "wind_speed_10m",
    "Wind Gusts (m/s)": "wind_gusts_10m",
    "Wind Direction (°)": "wind_direction_10m"
}

energy_types = {
    "Wind Production": ("production", "wind"),
    "Solar Production": ("production", "solar"),
    "Hydro Production": ("production", "hydro"),
    "Total Consumption": ("consumption", "All")
}

# Variable selectors
col1, col2 = st.columns(2)
with col1:
    weather_var_label = st.selectbox("Weather Variable", list(weather_variables.keys()))
    weather_var = weather_variables[weather_var_label]
    
with col2:
    energy_var_label = st.selectbox("Energy Variable", list(energy_types.keys()))
    energy_type, energy_group = energy_types[energy_var_label]

# Correlation parameters
col1, col2, col3 = st.columns(3)
with col1:
    window_size = st.slider("Window Size (hours)", min_value=24, max_value=720, value=168, step=24,
                           help="Size of the sliding window for correlation calculation")
with col2:
    lag = st.slider("Lag (hours)", min_value=-168, max_value=168, value=0, step=6,
                   help="Time shift: positive lag means weather leads energy, negative means energy leads weather")
with col3:
    resample_freq = st.selectbox("Data Resolution", 
                                  options=["Hourly", "Daily", "Weekly"],
                                  index=1,
                                  help="Resample data to reduce noise")

# Map resolution to pandas frequency
freq_map = {"Hourly": "H", "Daily": "D", "Weekly": "W"}
resample_to = freq_map[resample_freq]

st.markdown("---")

# Load data
with st.spinner(f"Loading weather data for {city_name}..."):
    weather_df = get_weather_data(lat, lon, year)

with st.spinner(f"Loading energy data for {chosen_area}..."):
    if energy_type == "production":
        energy_df = load_energy_data_v2()
    else:
        energy_df = load_consumption_data()
    
    # Filter by area and year
    energy_df = energy_df[energy_df['area'] == chosen_area].copy()
    energy_df['year'] = pd.to_datetime(energy_df['starttime']).dt.year
    energy_df = energy_df[energy_df['year'] == year].copy()
    
    # Filter by group
    group_col = 'productiongroup' if energy_type == "production" else 'consumptiongroup'
    if energy_group != "All":
        energy_df = energy_df[energy_df[group_col] == energy_group].copy()
    else:
        # Sum all groups
        energy_df = energy_df.groupby('starttime')['quantitykwh'].sum().reset_index()

if weather_df.empty:
    st.error("No weather data available.")
    st.stop()

if energy_df.empty:
    st.error("No energy data available for the selected parameters.")
    st.stop()

# Prepare time series
# Weather data already has time as index from get_weather_data()
weather_df = weather_df.sort_index()

energy_df['starttime'] = pd.to_datetime(energy_df['starttime'])
energy_df = energy_df.sort_values('starttime')

# Aggregate energy data to hourly (in case there are duplicates)
if 'quantitykwh' in energy_df.columns:
    energy_series = energy_df.groupby('starttime')['quantitykwh'].sum()
else:
    energy_series = energy_df.set_index('starttime')['quantitykwh']

# Get weather series
if weather_var not in weather_df.columns:
    st.error(f"Weather variable '{weather_var}' not found in data.")
    st.stop()

weather_series = weather_df[weather_var]

# Align data - find overlapping time range
start_time = max(weather_series.index.min(), energy_series.index.min())
end_time = min(weather_series.index.max(), energy_series.index.max())

weather_series = weather_series[(weather_series.index >= start_time) & (weather_series.index <= end_time)]
energy_series = energy_series[(energy_series.index >= start_time) & (energy_series.index <= end_time)]

# Resample to hourly frequency (fill missing values)
weather_series = weather_series.resample('H').mean().interpolate()
energy_series = energy_series.resample('H').sum()

# Now resample to selected resolution if not hourly
if resample_to != "H":
    weather_series = weather_series.resample(resample_to).mean()
    energy_series = energy_series.resample(resample_to).sum()
    
    # Adjust window size and lag for the new resolution
    if resample_to == "D":  # Daily
        window_size_adjusted = max(1, window_size // 24)
        lag_adjusted = lag // 24
    elif resample_to == "W":  # Weekly
        window_size_adjusted = max(1, window_size // 168)
        lag_adjusted = lag // 168
else:
    window_size_adjusted = window_size
    lag_adjusted = lag

# Apply lag to weather data
if lag_adjusted != 0:
    if resample_to == "H":
        weather_series_lagged = weather_series.copy()
        weather_series_lagged.index = weather_series_lagged.index + timedelta(hours=lag_adjusted)
    elif resample_to == "D":
        weather_series_lagged = weather_series.copy()
        weather_series_lagged.index = weather_series_lagged.index + timedelta(days=lag_adjusted)
    elif resample_to == "W":
        weather_series_lagged = weather_series.copy()
        weather_series_lagged.index = weather_series_lagged.index + timedelta(weeks=lag_adjusted)
else:
    weather_series_lagged = weather_series

# Calculate sliding window correlation
correlation = energy_series.rolling(window=window_size_adjusted, center=True).corr(weather_series_lagged)

# Create visualization
st.subheader(f"Sliding Window Correlation: {weather_var_label} vs {energy_var_label}")

# Create subplot figure
fig = go.Figure()

# Normalize series for visualization (z-score)
weather_norm = (weather_series - weather_series.mean()) / weather_series.std()
energy_norm = (energy_series - energy_series.mean()) / energy_series.std()

# Plot 1: Weather variable
fig.add_trace(go.Scatter(
    x=weather_norm.index,
    y=weather_norm.values,
    name=weather_var_label,
    line=dict(color='blue', width=1),
    yaxis='y1'
))

# Plot 2: Energy variable
fig.add_trace(go.Scatter(
    x=energy_norm.index,
    y=energy_norm.values,
    name=energy_var_label,
    line=dict(color='green', width=1),
    yaxis='y1'
))

# Plot 3: Correlation
fig.add_trace(go.Scatter(
    x=correlation.index,
    y=correlation.values,
    name='Correlation',
    line=dict(color='red', width=2),
    yaxis='y2'
))

# Add zero line for correlation
fig.add_hline(y=0, line_dash="dot", line_color="gray", yref='y2')

# Update layout with dual y-axes
fig.update_layout(
    height=600,
    hovermode='x unified',
    xaxis=dict(title="Time"),
    yaxis=dict(
        title="Normalized Values (Z-score)",
        side='left',
        range=[-3, 3]
    ),
    yaxis2=dict(
        title="Correlation",
        overlaying='y',
        side='right',
        range=[-1, 1],
        showgrid=False
    ),
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)')
)

st.plotly_chart(fig, use_container_width=True)

# Statistics
st.subheader("Correlation Statistics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Mean Correlation", f"{correlation.mean():.3f}")
with col2:
    st.metric("Max Correlation", f"{correlation.max():.3f}")
with col3:
    st.metric("Min Correlation", f"{correlation.min():.3f}")
with col4:
    st.metric("Std Deviation", f"{correlation.std():.3f}")

# Find extreme correlation periods
st.subheader("🔍 Extreme Correlation Periods")

# Find top 5 positive and negative correlation windows
correlation_sorted = correlation.dropna().sort_values()
top_negative = correlation_sorted.head(5)
top_positive = correlation_sorted.tail(5).iloc[::-1]

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Strongest Positive Correlations:**")
    for time, corr in top_positive.items():
        st.write(f"- {time.strftime('%Y-%m-%d %H:%M')}: {corr:.3f}")

with col2:
    st.markdown("**Strongest Negative Correlations:**")
    for time, corr in top_negative.items():
        st.write(f"- {time.strftime('%Y-%m-%d %H:%M')}: {corr:.3f}")

# Interpretation help
st.markdown("---")
st.markdown("""
### 📊 Interpretation Guide

- **Positive correlation**: When weather variable increases, energy variable tends to increase
- **Negative correlation**: When weather variable increases, energy variable tends to decrease
- **Near zero**: Little to no linear relationship in that time window

**Lag parameter**:
- **Positive lag**: Weather variable is shifted forward in time (weather "leads" energy response)
- **Negative lag**: Energy variable is shifted forward (energy "leads" weather)
- **Zero lag**: No time shift between variables

**Window size**: Larger windows smooth out short-term fluctuations, smaller windows show more variability.
""")

st.markdown("---")
st.caption(f"Data period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} | Resolution: {resample_freq} | Window: {window_size}h ({window_size_adjusted} {resample_to}) | Lag: {lag}h ({lag_adjusted} {resample_to})")
