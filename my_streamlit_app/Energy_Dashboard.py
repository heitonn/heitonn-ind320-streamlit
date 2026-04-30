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
    This dashboard investigates energy production and consumption across Norwegian price areas, 
    with a focus on how weather variables such as temperature, wind and snow conditions relate 
    to patterns in the power system.

    The project combines time series analysis, weather data, anomaly detection and forecasting 
    to make energy trends easier to explore.
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Focus", "Norway")
    st.write("Compare energy patterns across Norwegian price areas NO1–NO5.")

with col2:
    st.metric("Data type", "Time series")
    st.write("Explore production, consumption, weather variables and seasonal patterns.")

with col3:
    st.metric("Methods", "Analysis + ML")
    st.write("Includes correlation analysis, anomaly detection and forecasting.")

st.divider()

st.header("What you can explore")

st.markdown(
    """
    **Production and consumption**  
    See how energy use and generation vary over time and between regions.

    **Weather effects**  
    Investigate how wind, temperature and snow-related variables connect to production and demand.

    **Seasonality and trends**  
    Use decomposition and time series tools to separate long-term trends from recurring patterns.

    **Anomalies and forecasting**  
    Identify unusual periods and experiment with forecasting using weather as external input.
    """
)

st.divider()

st.header("Why this project matters")

st.markdown(
    """
    Norway’s power system is highly dependent on geography, weather and regional differences. 
    A cold period in one area, strong wind in another, or snow conditions affecting hydropower 
    can all influence the balance between production and consumption.

    This dashboard is built to make those relationships visible.
    """
)

st.info(
    "Use the sidebar to navigate between analysis pages."
)
