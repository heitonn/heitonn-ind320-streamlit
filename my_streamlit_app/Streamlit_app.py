import streamlit as st

st.set_page_config(page_title="Energy & Weather Dashboard", page_icon="📊", layout="wide")

st.title("📊 Energy & Weather Analytics Dashboard")

st.markdown("""
Welcome to the comprehensive Energy & Weather Analytics platform for Norwegian price areas.

This dashboard provides interactive tools for exploring, analyzing, and forecasting energy production and consumption 
patterns in relation to weather conditions across Norway's five price areas (NO1-NO5).
""")

st.markdown("---")

# Three-column layout for the three main sections
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🗺️ Exploration")
    st.markdown("""
    **Start your analysis here:**
    - Interactive map with price areas
    - Energy production & consumption overview
    - Weather data visualization
    
    Get familiar with the data through interactive charts and regional comparisons.
    """)
    if st.button("📍 Go to Interactive Map", use_container_width=True, type="primary"):
        st.switch_page("pages/01_Interactive_Map.py")

with col2:
    st.subheader("🔍 Analysis & Patterns")
    st.markdown("""
    **Deep-dive analysis:**
    - Energy decomposition (trends, seasonality)
    - Weather anomaly detection
    - Snow drift calculations
    - Weather-energy correlations
    
    Discover patterns and relationships in the data.
    """)
    if st.button("📈 Explore Analysis Tools", use_container_width=True):
        st.switch_page("pages/04_Energy_Decomposition.py")

with col3:
    st.subheader("🔮 Forecasting")
    st.markdown("""
    **Predictive modeling:**
    - SARIMAX forecasting
    - Configurable parameters
    - Exogenous weather variables
    - Confidence intervals
    
    Predict future energy production and consumption.
    """)
    if st.button("🎯 Create Forecast", use_container_width=True):
        st.switch_page("pages/08_Energy_Forecast.py")

st.markdown("---")

st.markdown("""
### 💡 Quick Start Guide

1. **Select a region** on the Interactive Map page
2. **Explore the data** using the visualization tools
3. **Analyze patterns** with decomposition and correlation tools
4. **Create forecasts** using the SARIMAX model

Use the sidebar to navigate between different pages. Your selected region will be remembered across pages.
""")

st.markdown("---")
st.caption("Data sources: Elhub API (Energy), Open-Meteo Archive API (Weather) | 2021-2024")