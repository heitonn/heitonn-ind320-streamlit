import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

#imports for STL and spectrogram
from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram

# imports from utils
from utils.load_energy_data import load_energy_data_v2
from utils.ui_helpers import choose_price_area

# page title and header
st.set_page_config(page_title="Energy Decomposition", layout="wide", page_icon="📈")
st.title("📈 Energy Decomposition")
st.markdown("Analyze energy trends, seasonality, and patterns using STL decomposition and spectrograms.")
st.info("💡 Tip: Select your region on the Interactive Map page first, then choose a production group to analyze.")

# load energy data from utils/load_energy_data.py
df = load_energy_data_v2()

# choosing area using utils/choose
chosen_area, row = choose_price_area()

# select production group
all_groups = df['productiongroup'].unique().tolist()
selected_group = st.selectbox("Select production group:", all_groups)

# Creating tabs for STL and Spectrogram
tab1, tab2 = st.tabs(["STL Decomposition", "Spectrogram"])

with tab1:
    st.subheader(f"STL Decomposition for {selected_group} in {chosen_area}")  
    
    # Filter data
    df_filtered = df[(df['area'] == chosen_area) & (df['productiongroup'] == selected_group)].copy()
    df_filtered = df_filtered.sort_values('starttime')
    
    # Create time series
    ts = df_filtered.set_index('starttime')['quantitykwh']

    # Check if time series is long enough and perform STL
    if len(ts) < 24:
        st.write("Time series too short for STL decomposition.")
    else:
        stl = STL(ts, period=24, seasonal=13, trend=25, robust=False)
        result = stl.fit()

        # Create Plotly subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
            vertical_spacing=0.08
        )
        
        # Add traces
        fig.add_trace(
            go.Scatter(x=ts.index, y=ts.values, mode='lines', name='Observed', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=result.trend.index, y=result.trend.values, mode='lines', name='Trend', line=dict(color='orange')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=result.seasonal.index, y=result.seasonal.values, mode='lines', name='Seasonal', line=dict(color='green')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=result.resid.index, y=result.resid.values, mode='lines', name='Residual', line=dict(color='red')),
            row=4, col=1
        )
        
        # Update layout
        fig.update_xaxes(title_text="Time", row=4, col=1)
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode='x unified',
            margin=dict(l=40, r=40, t=80, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"Spectrogram for {selected_group} in {chosen_area}")
    
    # Filter data and create time series with timestamps
    ts_series = df_filtered.set_index('starttime')['quantitykwh']
    ts = ts_series.values
    
    # Check if time series is long enough and compute spectrogram
    if len(ts) < 24:
        st.write("Time series too short for spectrogram.")
    else:
        f, t_vals, Sxx = spectrogram(ts, fs=1, nperseg=24, noverlap=12)
        Sxx_plot = 10 * np.log10(Sxx + 1e-10)
        
        # Create Plotly heatmap
        fig = go.Figure(data=go.Heatmap(
            z=Sxx_plot,
            x=t_vals,
            y=f,
            colorscale='Viridis',
            colorbar=dict(title="Power (dB)")
        ))
        
        fig.update_layout(
            title=f"Spectrogram of {selected_group} in {chosen_area}",
            xaxis_title="Time (hours)",
            yaxis_title="Frequency (1/hour)",
            xaxis2=dict(
                title="Date",
                overlaying='x',
                side='top',
                tickmode='array',
                showgrid=False
            ),
            height=500,
            margin=dict(l=40, r=40, t=80, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
