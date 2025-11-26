import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# imports for DCT and LOF
from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor

# imports from utils
from utils.constants import city_data_df
from utils.weather_data_fetcher import get_weather_data
from utils.ui_helpers import choose_price_area

st.set_page_config(page_title="Weather Anomalies", layout="wide", page_icon="⚠️")
st.title("⚠️ Weather Anomalies Detection")
st.markdown("Detect unusual weather patterns using Statistical Process Control (SPC) for temperature and Local Outlier Factor (LOF) for precipitation.")
st.info("💡 Tip: Adjust the detection parameters to find different types of anomalies.")

chosen_area, row =  choose_price_area()

# Change area here
chosen_area = st.session_state.get("chosen_area")

# Fetch the row 
row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]

# Year selection
year = st.selectbox("Select Year", [2021, 2022, 2023, 2024], index=0)

# Load data 
df = get_weather_data(row["Latitude"], row["Longitude"], year=year)
df = df.reset_index().rename(columns={"time":"date"})

# Tabs for temperature and precipitation
tab1, tab2 = st.tabs(["Temperature (SPC)", "Precipitation (LOF)"])

with tab1:
    st.subheader("Temperature - Seasonal Adjusted with DCT and SPC")
    
    # Sliders for parameters for SPC
    cutoff = st.slider("High-pass DCT cutoff", min_value=1, max_value=200, value=50)
    n_std = st.slider("Number of MADs for SPC boundaries", min_value=1, max_value=5, value=3)

    # Compute seasonal adjusted temperature using DCT
    temps = df["temperature_2m"].to_numpy()
    dates = pd.to_datetime(df["date"])
    temps_dct = dct(temps, norm='ortho')
    temps_dct[:cutoff] = 0  # High-pass filter - set low frequencies to 0 (not 50)
    temps_satv = idct(temps_dct, norm='ortho')
    
    # Robust statistics with MAD (on seasonally adjusted)
    median_satv = np.median(temps_satv)
    mad_satv = np.median(np.abs(temps_satv - median_satv))
    upper_limit_satv = median_satv + n_std * mad_satv
    lower_limit_satv = median_satv - n_std * mad_satv
    
    # Trim edge effects (first and last 0.25% of data)
    # Edge effects can distort the detection, so we exclude them
    edge_trim = int(len(temps_satv) * 0.0025)
    temps_satv_trimmed = temps_satv.copy()
    temps_satv_trimmed[:edge_trim] = np.nan
    temps_satv_trimmed[-edge_trim:] = np.nan
    
    outliers = (temps_satv_trimmed > upper_limit_satv) | (temps_satv_trimmed < lower_limit_satv)
    
    # Calculate boundaries relative to original temperature
    # The boundaries follow the seasonal pattern (inverse of high-pass)
    temps_seasonal = temps - temps_satv  # Extract seasonal component
    upper_limit_original = temps_seasonal + upper_limit_satv
    lower_limit_original = temps_seasonal + lower_limit_satv
    
    # Plotting temperature with outliers using Plotly
    fig = go.Figure()
    
    # Add temperature trace
    fig.add_trace(go.Scatter(
        x=dates, y=temps,
        mode='lines',
        name='Temperature',
        line=dict(color='steelblue', width=1.5),
        opacity=0.7
    ))
    
    # Add outliers
    fig.add_trace(go.Scatter(
        x=dates[outliers], y=temps[outliers],
        mode='markers',
        name='Outliers',
        marker=dict(color='red', size=6)
    ))
    
    # Add SPC boundaries (following original temperature pattern)
    fig.add_trace(go.Scatter(
        x=dates, y=upper_limit_original,
        mode='lines',
        name='Upper boundary',
        line=dict(color='green', width=2, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, y=lower_limit_original,
        mode='lines',
        name='Lower boundary',
        line=dict(color='green', width=2, dash='dash')
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Temperature anomalies in {chosen_area}",
        xaxis_title="Date",
        yaxis_title="Temperature (°C)",
        height=500,
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary of outliers
    st.write(f"Detected {outliers.sum()} outliers out of {len(df)} points")

with tab2:
    st.subheader("Precipitation with Local Outlier Factor (LOF)")

    # Sliders for LOF parameters neighbors and contamination
    n_neighbors = st.slider("LOF neighbors", min_value=5, max_value=100, value=50)
    contamination = st.slider("LOF contamination", min_value=0.001, max_value=0.05, value=0.01, step=0.001)

    # Compute LOF
    X = df["precipitation"].values.reshape(-1,1)
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    y_pred = lof.fit_predict(X)
    anomalies = y_pred == -1
    outlier_df = df.loc[anomalies, ["date","precipitation"]]

    # Plotting precipitation with outliers using Plotly
    fig = go.Figure()
    
    # Add precipitation trace
    fig.add_trace(go.Scatter(
        x=dates, y=df["precipitation"],
        mode='lines',
        name='Precipitation',
        line=dict(color='steelblue', width=1.5),
        opacity=0.7
    ))
    
    # Add anomalies
    fig.add_trace(go.Scatter(
        x=outlier_df["date"], y=outlier_df["precipitation"],
        mode='markers',
        name='LOF anomalies',
        marker=dict(color='red', size=6)
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Precipitation anomalies in {chosen_area}",
        xaxis_title="Date",
        yaxis_title="Precipitation (mm)",
        height=500,
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.write(f"Detected {len(outlier_df)} outliers out of {len(df)} points")
