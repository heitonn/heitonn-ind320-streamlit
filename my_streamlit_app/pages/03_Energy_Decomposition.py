import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram
from utils.load_energy_data import load_energy_data
from utils.ui_helpers import choose_price_area

st.set_page_config(page_title="Energy Decomposition", layout="wide")
st.header("Energy Data Decomposition and Spectrogram")

# load energy data
df = load_energy_data()

# --- AREA SELECTION ---
chosen_area, row = choose_price_area()

# --- PRODUCTION GROUP SELECTION ---
all_groups = df['productiongroup'].unique().tolist()
selected_group = st.selectbox("Select production group:", all_groups)

# --- TABS ---
tab1, tab2 = st.tabs(["STL Decomposition", "Spectrogram"])

with tab1:
    st.subheader(f"STL Decomposition for {selected_group} in {chosen_area}")  # <-- bruk chosen_area
    
    # Filter data
    df_filtered = df[(df['area'] == chosen_area) & (df['productiongroup'] == selected_group)].copy()
    df_filtered = df_filtered.sort_values('starttime')
    
    ts = df_filtered.set_index('starttime')['quantitykwh']
    if len(ts) < 24:
        st.write("Time series too short for STL decomposition.")
    else:
        stl = STL(ts, period=24, seasonal=13, trend=25, robust=False)
        result = stl.fit()
        
        fig, axes = plt.subplots(4, 1, figsize=(10,8), sharex=True)
        axes[0].plot(ts, label="Observed")
        axes[0].legend()
        axes[1].plot(result.trend, label="Trend", color="orange")
        axes[1].legend()
        axes[2].plot(result.seasonal, label="Seasonal", color="green")
        axes[2].legend()
        axes[3].plot(result.resid, label="Residual", color="red")
        axes[3].legend()
        plt.xlabel("Time")
        st.pyplot(fig)

with tab2:
    st.subheader(f"Spectrogram for {selected_group} in {chosen_area}")  # <-- bruk chosen_area
    
    ts = df_filtered.set_index('starttime')['quantitykwh'].values
    if len(ts) < 24:
        st.write("Time series too short for spectrogram.")
    else:
        f, t_vals, Sxx = spectrogram(ts, fs=1, nperseg=24, noverlap=12)
        Sxx_plot = 10 * np.log10(Sxx + 1e-10)
        
        fig, ax = plt.subplots(figsize=(12,5))
        c = ax.pcolormesh(t_vals, f, Sxx_plot, shading='gouraud')
        ax.set_ylabel("Frequency (1/hour)")
        ax.set_xlabel("Time (hours)")
        plt.title(f"Spectrogram of {selected_group} in {chosen_area}")
        fig.colorbar(c, ax=ax, label="Power (dB)")
        st.pyplot(fig)
