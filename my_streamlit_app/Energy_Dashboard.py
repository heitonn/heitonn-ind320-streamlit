import streamlit as st 

st.set_page_config(page_title="Energy & Weather Dashboard", layout="wide")

col_title, col_stats = st.columns([2,1])

with col_title:
    st.title("⚡ Energy & Weather Analytics")
    st.caption("Explore production, consumption and weather patterns across Norwegian price areas")

with col_stats:
    st.metric("Areas", "NO1–NO5")
    st.metric("Resolution", "Hourly")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🔍 Exploration")
    st.markdown("""
    - Production & consumption overview  
    - Daily trends and comparisons  
    - Weather visualisation  
    """)
    st.button("Go to Energy Overview", use_container_width=True)

with col2:
    st.subheader("📈 Analysis")
    st.markdown("""
    - Decomposition  
    - Anomaly detection  
    - Correlations  
    """)
    st.button("Explore Analysis Tools", use_container_width=True)

with col3:
    st.subheader("🔮 Forecasting")
    st.markdown("""
    - SARIMAX models  
    - Exogenous variables  
    - Confidence intervals  
    """)
    st.button("Create Forecast", use_container_width=True)

st.divider()
