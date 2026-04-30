import streamlit as st

st.set_page_config(
    page_title="Norwegian Energy Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.title("Norwegian Energy Dashboard ⚡")
st.subheader("Explore how weather, geography and demand shape Norway’s power system.")

st.markdown(
    """
    Norway’s power system is highly dependent on geography, weather and regional differences. 
    Cold periods, strong wind, or extreme weather events can all influence the balance 
    between production and consumption.

    This dashboard combines energy and weather time series to make these relationships visible, 
    highlighting patterns in production, consumption and regional variation over time.
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Data", "Time series")
    st.write("Energy production, consumption and weather variables over time.")

with col2:
    st.metric("Methods", "Analysis + ML")
    st.write("Correlation, anomaly detection and forecasting.")

with col3:
    st.metric("Scope", "5 price areas")
    st.write("NO1–NO5 with production by source and sector-level consumption.")

st.divider()

st.header("What you can explore")

st.markdown(
    """
    **Production and consumption**  
    See how energy use and generation vary over time and between regions.

    **Weather data**  
    Explore wind, temperature and precipitation as time series.

    **Weather analysis**  
    Analyze anomalies and derived features such as snow drift.

    **Energy time series analysis**  
    Examine production using spectrograms and STL decomposition.

    **Weather–energy relationships**  
    Investigate correlations and forecasting models using weather as exogenous input.
    """
)

st.divider()

st.caption(
    "Data sources: Energy data from Elhub. Weather data from Open-Meteo. "
    "Production includes hydro, wind, solar, thermal and other sources. "
    "Consumption is split into household, cabin and commercial sectors."
)


st.divider()
