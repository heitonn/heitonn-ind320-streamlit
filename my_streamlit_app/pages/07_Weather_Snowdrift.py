import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.weather_data_fetcher import get_weather_data
from utils.constants import city_data_df
from utils.snowdrift_calculations import (
    compute_yearly_results,
    compute_average_sector
)

# Page config
st.set_page_config(page_title="Snow Drift Analysis", layout="wide")
st.header("❄️ Snow Drift Analysis")

st.markdown("""
**Snow drift** is the amount of snow transported by wind. This analysis calculates how much snow 
is blown around at your location, which is important for:
- Planning snow fences to protect roads and buildings
- Understanding where snow accumulates
- Designing structures in snowy areas
""")

st.divider()

# Check if a price area has been selected
if "chosen_area" not in st.session_state or st.session_state.chosen_area is None:
    st.warning("""
    ### ⚠️ No price area selected
    
    Please go to the **Energy Map** page and select a price area by clicking one of the city buttons.
    
    Then come back to this page to analyze snow drift at that location.
    """)
    st.stop()

# Get coordinates for the selected price area
chosen_area = st.session_state.chosen_area
area_info = city_data_df[city_data_df['PriceArea'] == chosen_area].iloc[0]
lat = area_info['Latitude']
lon = area_info['Longitude']
city = area_info['City']

st.success(f"📍 Analyzing snow drift for **{chosen_area} - {city}** ({lat:.2f}°N, {lon:.2f}°E)")

st.divider()

# ============ PARAMETERS ============
st.subheader("Parameters")

col1, col2 = st.columns(2)

with col1:
    # Year range selection
    st.markdown("#### Year Range")
    st.caption("Select the range of years to analyze (season = July 1 to June 30)")
    
    year_start = st.number_input(
        "Start Year",
        min_value=1940,
        max_value=2024,
        value=2021,
        step=1
    )
    
    year_end = st.number_input(
        "End Year",
        min_value=year_start,
        max_value=2024,
        value=2024,
        step=1
    )
    
    if year_end < year_start:
        st.error("End year must be greater than or equal to start year!")
        st.stop()

with col2:
    # Snow transport parameters
    st.markdown("#### Snow Transport Parameters")
    st.caption("Parameters for Tabler (2003) calculations")
    
    T = st.number_input(
        "Maximum transport distance (m)",
        min_value=100,
        max_value=10000,
        value=3000,
        step=100,
        help="Maximum distance snow can be transported"
    )
    
    F = st.number_input(
        "Fetch distance (m)",
        min_value=1000,
        max_value=100000,
        value=30000,
        step=1000,
        help="Upwind distance over which wind can accelerate"
    )
    
    theta = st.slider(
        "Relocation coefficient",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Fraction of snow that gets relocated"
    )

st.divider()

# ============ DATA LOADING ============
@st.cache_data(show_spinner=True)
def load_multi_year_weather_data(latitude, longitude, start_year, end_year):
    """
    Load weather data for multiple years using the existing get_weather_data function.
    The cache ensures we don't make redundant API calls.
    """
    years = list(range(start_year, end_year + 1))
    df = get_weather_data(latitude, longitude, year=years)
    
    # Reset index to make 'time' a column
    df = df.reset_index()
    
    # Define season: if month >= 7, season = current year; otherwise, season = previous year
    df['season'] = df['time'].apply(
        lambda dt: dt.year if dt.month >= 7 else dt.year - 1
    )
    
    return df

# Load data with spinner
with st.spinner(f"Loading weather data for {year_start}-{year_end}..."):
    try:
        df = load_multi_year_weather_data(lat, lon, year_start, year_end)
        st.success(f"✓ Loaded {len(df):,} hourly observations")
    except Exception as e:
        st.error(f"Error loading weather data: {e}")
        st.info("""
        **Note about Open-Meteo API limits:**
        - The free tier allows 10,000 API calls per day
        - Streamlit caches the data, so you won't make new API calls unless:
          - You clear the cache
          - You restart the app
          - The cache expires (default: 1 hour)
        - Each year requires 1 API call
        """)
        st.stop()

st.divider()

# ============ CALCULATIONS ============
with st.spinner("Calculating snow drift..."):
    yearly_results = compute_yearly_results(df, T, F, theta)
    avg_sectors = compute_average_sector(df)

if yearly_results.empty:
    st.error("No complete seasons found in the selected year range.")
    st.stop()

# ============ RESULTS DISPLAY ============
st.subheader("📊 Snow Drift Results")

st.markdown("""
**Qt (Snow Transport)** is the amount of snow blown by wind, measured in **tonnes per meter** (tonnes/m).
- Higher values = more snow gets transported by wind
- This tells you how much snow drift to expect each winter season
""")

# Overall statistics
overall_avg_kg = yearly_results['Qt (kg/m)'].mean()
overall_avg_tonnes = overall_avg_kg / 1000

col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.metric(
        "Average Snow Drift",
        f"{overall_avg_tonnes:.1f} tonnes/m",
        help="Average amount of snow transported per winter season"
    )
with col_stat2:
    max_qt = yearly_results['Qt (kg/m)'].max() / 1000
    max_season = yearly_results.loc[yearly_results['Qt (kg/m)'].idxmax(), 'season']
    st.metric("Highest Winter", f"{max_qt:.1f} tonnes/m", delta=f"{max_season}")
with col_stat3:
    min_qt = yearly_results['Qt (kg/m)'].min() / 1000
    min_season = yearly_results.loc[yearly_results['Qt (kg/m)'].idxmin(), 'season']
    st.metric("Lowest Winter", f"{min_qt:.1f} tonnes/m", delta=f"{min_season}")

st.divider()

# ============ YEARLY PLOT ============
st.subheader("📈 Snow Drift by Winter Season")
st.caption("Each bar shows how much snow was transported during that winter (July to June)")

# Prepare data for plotting
yearly_results['Qt (tonnes/m)'] = yearly_results['Qt (kg/m)'] / 1000

fig_yearly = go.Figure()

fig_yearly.add_trace(go.Bar(
    x=yearly_results['season'],
    y=yearly_results['Qt (tonnes/m)'],
    name='Qt (tonnes/m)',
    marker_color='lightblue',
    hovertemplate='<b>%{x}</b><br>Qt: %{y:.1f} tonnes/m<extra></extra>'
))

# Add average line
fig_yearly.add_trace(go.Scatter(
    x=yearly_results['season'],
    y=[overall_avg_tonnes] * len(yearly_results),
    mode='lines',
    name='Average',
    line=dict(color='red', dash='dash', width=2),
    hovertemplate=f'Average: {overall_avg_tonnes:.1f} tonnes/m<extra></extra>'
))

fig_yearly.update_layout(
    xaxis_title="Season (July-June)",
    yaxis_title="Snow Transport Qt (tonnes/m)",
    hovermode='x unified',
    showlegend=True,
    height=400
)

st.plotly_chart(fig_yearly, use_container_width=True)

# Show control type for each season
with st.expander("📋 What limits the snow drift?"):
    st.markdown("""
    Snow drift can be limited by two factors:
    - **Wind controlled**: There's plenty of snow, but not enough wind to blow it around
    - **Snowfall controlled**: There's plenty of wind, but not enough snow to transport
    """)
    display_df = yearly_results[['season', 'Qt (tonnes/m)', 'Control']].copy()
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "season": "Season",
            "Qt (tonnes/m)": st.column_config.NumberColumn(
                "Qt (tonnes/m)",
                format="%.1f"
            ),
            "Control": "Limiting Factor"
        }
    )

st.divider()

# ============ WIND ROSE ============
st.subheader("🌹 Which Direction Does the Snow Come From?")

st.markdown("""
The **wind rose** shows which wind directions transport the most snow:
- Each "petal" represents a compass direction (N, NE, E, SE, etc.)
- Longer petals = more snow transported from that direction
""")

# Convert sectors from kg/m to tonnes/m
avg_sectors_tonnes = np.array(avg_sectors) / 1000.0

# Create polar plot
num_sectors = 16
angles = np.deg2rad(np.arange(0, 360, 360/num_sectors))
directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
              'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

# Create bar chart in polar coordinates
fig_rose = go.Figure()

fig_rose.add_trace(go.Barpolar(
    r=avg_sectors_tonnes,
    theta=np.rad2deg(angles),
    width=[360/num_sectors] * num_sectors,
    marker=dict(
        color=avg_sectors_tonnes,
        colorscale='Blues',
        showscale=True,
        colorbar=dict(title="tonnes/m")
    ),
    hovertemplate='<b>%{text}</b><br>Transport: %{r:.2f} tonnes/m<extra></extra>',
    text=directions
))

fig_rose.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, showticklabels=True),
        angularaxis=dict(
            direction='clockwise',
            period=360,
            tickmode='array',
            tickvals=np.rad2deg(angles),
            ticktext=directions
        )
    ),
    showlegend=False,
    height=600
)

st.plotly_chart(fig_rose, use_container_width=True)

# ============ INFO SECTION ============
st.divider()

with st.expander("ℹ️ How Are These Calculations Done?"):
    st.markdown("""
    ### Tabler (2003) Snow Drift Method
    
    This analysis calculates snow drift using the scientifically validated Tabler (2003) method.
    
    **What is Qt (Snow Transport)?**
    - Qt = the amount of snow blown by wind, measured in tonnes per meter (tonnes/m)
    - It combines wind speed and snowfall amount
    - Higher Qt = more snow drift problems
    
    **Winter Season Definition:**
    - Season runs from **July 1 to June 30** (not calendar year)
    - Example: "2021-2022" means July 1, 2021 to June 30, 2022
    - This captures the complete winter period
    
    **What Controls Snow Drift?**
    1. **Wind controlled**: Lots of snow available, but wind isn't strong enough to move it all
    2. **Snowfall controlled**: Strong winds, but not enough snow to transport
    
    **Data Source:**
    - Hourly weather data from Open-Meteo Archive API
    - Includes: temperature, precipitation, wind speed, wind direction
    - Snow is counted when temperature < 1°C
    
    **API Usage Note:**
    - Data is cached for 1 hour to minimize API calls
    - Free tier allows 10,000 calls/day (each year = 1 call)
    """)
