import streamlit as st

st.set_page_config(page_title="Energy & Weather Dashboard", page_icon="📊", layout="wide")

st.title("📊 Energy & Weather Analytics Dashboard")

st.markdown("""
Welcome to the Energy & Weather Analytics platform for Norwegian price areas.
""")

st.markdown("---")

# Three-column layout for the three main sections
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Exploration")
    st.markdown("""
    **Start your analysis here:**
    - Interactive map with price areas
    - Energy production & consumption overview
    - Weather data visualization
    
    Get familiar with the data through interactive charts and regional comparisons.
    """)
    if st.button("Go to Interactive Map", use_container_width=True, type="primary"):
        st.switch_page("pages/01_Explore_Map.py")

with col2:
    st.subheader("Analysis & Patterns")
    st.markdown("""
    **Deep-dive analysis:**
    - Energy decomposition (trends, seasonality)
    - Weather anomaly detection
    - Snow drift calculations
    - Weather-energy correlations
    
    Discover patterns and relationships in the data.
    """)
    if st.button("Explore Analysis Tools", use_container_width=True):
        st.switch_page("pages/04_Analyze_Energy_Decomposition.py")

with col3:
    st.subheader("Forecasting")
    st.markdown("""
    **Predictive modeling:**
    - SARIMAX forecasting
    - Configurable parameters
    - Exogenous weather variables
    - Confidence intervals
    
    Predict future energy production and consumption.
    """)
    if st.button("Create Forecast", use_container_width=True):
        st.switch_page("pages/08_Predict_Energy_Forecast.py")

st.markdown("---")