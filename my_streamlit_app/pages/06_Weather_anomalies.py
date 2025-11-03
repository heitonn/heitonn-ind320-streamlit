import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor
from utils.constants import city_data_df
from utils.data_fetcher import get_weather_data

st.set_page_config(page_title="Anomalies and  outliers", layout="wide")

st.header("Weather Anomalies Detection")

# --- Select area ---
chosen_area = st.session_state.get("chosen_area", "NO5")
row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]
st.write(f"**Currently selected area:** {chosen_area} ({row['City']})")

# Optionally allow user to change area here
chosen_area = st.session_state.get("chosen_area", "NO1")

# Finn kun prisområder som finnes i city_data_df
available_areas = city_data_df["PriceArea"].tolist()

# Lag labels kun for de tilgjengelige områdene
areas = [area for area in [f"NO{i}" for i in range(1, 6)] if area in available_areas]
labels = [f"{area} – {city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]}" for area in areas]

# Sett default index
default_index = areas.index(chosen_area) if chosen_area in areas else 0

selected_label = st.radio("Select price area:", labels, index=default_index, horizontal=True)

# Hent NOx
chosen_area = selected_label.split(" – ")[0]  
st.session_state["chosen_area"] = chosen_area

# Hent raden trygt
row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]

# --- Load data ---
df = get_weather_data(row["Latitude"], row["Longitude"], year=2021)
df = df.reset_index().rename(columns={"time":"date"})

# --- Tabs ---
tab1, tab2 = st.tabs(["Temperature (SPC)", "Precipitation (LOF)"])

with tab1:
    st.subheader("Temperature SPC Outliers")
    
    # Parameters
    cutoff = st.slider("High-pass DCT cutoff", min_value=1, max_value=200, value=50)
    n_std = st.slider("Number of MADs for SPC boundaries", min_value=1, max_value=5, value=3)

    # Compute SPC
    temps = df["temperature_2m"].to_numpy()
    dates = pd.to_datetime(df["date"])
    temps_dct = dct(temps, norm='ortho')
    temps_dct[:cutoff] = 0
    temps_satv = idct(temps_dct, norm='ortho')
    
    median_satv = np.median(temps_satv)
    mad_satv = np.median(np.abs(temps_satv - median_satv))
    upper_limit = median_satv + n_std * mad_satv
    lower_limit = median_satv - n_std * mad_satv
    outliers = (temps_satv > upper_limit) | (temps_satv < lower_limit)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(dates, temps, color="steelblue", alpha=0.7, label="Temperature")
    ax.scatter(dates[outliers], temps[outliers], color="red", s=10, label="Outliers")
    ax.axhline(median_satv + upper_limit, color="green", linestyle="--", label="SPC boundaries")
    ax.axhline(median_satv + lower_limit, color="green", linestyle="--")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"Temperature anomalies in {chosen_area}")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
    
    st.write(f"Detected {outliers.sum()} outliers out of {len(df)} points")

with tab2:
    st.subheader("Precipitation LOF Outliers")
    
    n_neighbors = st.slider("LOF neighbors", min_value=5, max_value=100, value=50)
    contamination = st.slider("LOF contamination", min_value=0.001, max_value=0.05, value=0.01, step=0.001)

    # LOF
    X = df["precipitation"].values.reshape(-1,1)
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    y_pred = lof.fit_predict(X)
    anomalies = y_pred == -1
    outlier_df = df.loc[anomalies, ["date","precipitation"]]

    # Plot
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(dates, df["precipitation"], color="steelblue", alpha=0.7, label="Precipitation")
    ax.scatter(outlier_df["date"], outlier_df["precipitation"], color="red", s=10, label="LOF anomalies")
    ax.set_xlabel("Date")
    ax.set_ylabel("Precipitation (mm)")
    ax.set_title(f"Precipitation anomalies in {chosen_area}")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.write(f"Detected {len(outlier_df)} outliers out of {len(df)} points")
