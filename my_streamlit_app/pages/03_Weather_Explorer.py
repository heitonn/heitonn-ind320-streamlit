import streamlit as st
import pandas as pd
import plotly.express as px

# imports from utils
from utils.constants import city_data_df
from utils.weather_data_fetcher import get_weather_data
from utils.ui_helpers import choose_price_area

st.set_page_config(page_title="Weather Explorer", layout="wide", page_icon="🌤️")
st.title("🌤️ Weather Data Explorer")

st.markdown("Explore historical weather data for selected Norwegian price areas from 2021-2024.")
st.info("💡 Tip: Select your region on the Interactive Map page for consistent analysis across all pages.")

# Area selection
chosen_area, row = choose_price_area()

# Year selection
year = st.selectbox("Select Year", [2021, 2022, 2023, 2024], index=0)

# Fetch weather data
df = get_weather_data(row["Latitude"], row["Longitude"], year=year)

# Mapping column names to user-friendly labels
column_names = {
    "temperature_2m": "Temperature (°C)",
    "precipitation": "Precipitation (mm)",
    "wind_speed_10m": "Wind Speed (m/s)",
    "wind_gusts_10m": "Wind Gusts (m/s)",
    "wind_direction_10m": "Wind Direction (°)"
}
df.columns = [column_names.get(col, col) for col in df.columns]

# Create tabs
tab1, tab2 = st.tabs(["📊 Data Visualizer", "📅 January Overview"])

with tab1:
    st.subheader("Interactive Weather Visualization")
    st.markdown("Select variables and time range to explore weather patterns.")
    
    # Column selection
    options = list(df.columns) + ["All columns"]
    selected_col = st.selectbox("Select column(s) to plot:", options)
    
    # Month range selection
    months = sorted(df.index.to_period("M").unique().strftime("%Y-%m"))
    selected_months = st.select_slider(
        "Select months range:",
        options=months,
        value=(months[0], months[-1])
    )
    
    # Filter data
    start, end = pd.Period(selected_months[0]), pd.Period(selected_months[1])
    mask = (df.index.to_period("M") >= start) & (df.index.to_period("M") <= end)
    df_subset = df.loc[mask]
    
    # Plot with Plotly
    if selected_col == "All columns":
        fig = px.line(
            df_subset.reset_index(),
            x='time',
            y=df_subset.columns.tolist(),
            title=f"Weather Data - {chosen_area} ({year})",
            labels={'value': 'Value', 'time': 'Time', 'variable': 'Variable'}
        )
    else:
        fig = px.line(
            df_subset.reset_index(),
            x='time',
            y=selected_col,
            title=f"{selected_col} - {chosen_area} ({year})",
            labels={selected_col: selected_col, 'time': 'Time'}
        )
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=selected_col if selected_col != "All columns" else "Value",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("January Weather Overview")
    st.markdown("Quick overview of January weather patterns with inline sparklines.")
    
    # Filter January data
    january = df.loc[f"{year}-01"]
    
    # Create table with sparklines
    january_table = pd.DataFrame({
        "Temperature (°C)": [january["Temperature (°C)"].values],
        "Precipitation (mm)": [january["Precipitation (mm)"].values],
        "Wind Speed (m/s)": [january["Wind Speed (m/s)"].values],
        "Wind Gusts (m/s)": [january["Wind Gusts (m/s)"].values],
        "Wind Direction (°)": [january["Wind Direction (°)"].values],
    })
    
    # Transpose and format
    january_table = january_table.T.reset_index()
    january_table.columns = ["Variable", "Values"]
    
    # Display with line chart column
    st.dataframe(
        january_table,
        column_config={
            "Values": st.column_config.LineChartColumn(f"January {year}"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Summary statistics
    st.markdown("### January Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Temperature", f"{january['Temperature (°C)'].mean():.1f}°C")
    with col2:
        st.metric("Total Precipitation", f"{january['Precipitation (mm)'].sum():.1f} mm")
    with col3:
        st.metric("Avg Wind Speed", f"{january['Wind Speed (m/s)'].mean():.1f} m/s")
    with col4:
        st.metric("Max Wind Gust", f"{january['Wind Gusts (m/s)'].max():.1f} m/s")
