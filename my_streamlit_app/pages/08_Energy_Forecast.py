import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings('ignore')

# Import utility functions
from utils.ui_helpers import choose_price_area
from utils.load_energy_data import load_energy_data_v2, load_consumption_data
from utils.weather_data_fetcher import get_weather_data
from utils.constants import city_data_df

st.set_page_config(page_title="Energy Forecast", layout="wide", page_icon="🔮")
st.title("🔮 SARIMAX Energy Forecasting")

st.markdown("""
**Forecast energy production or consumption using SARIMAX** (Seasonal AutoRegressive Integrated Moving Average with eXogenous variables).

**How to use:**
1. Select an energy variable (production type or consumption)
2. Choose training period and forecast horizon
3. Adjust SARIMAX parameters in the sidebar - start with default values (1,1,1)(1,0,1,24)
4. Optionally add weather variables as exogenous inputs
5. Click "Run Forecast" to train the model and see predictions with confidence intervals

**Tips:**
- Larger p, q values capture more complex patterns but may overfit
- d=1 or d=2 helps with trending data
- s=24 for daily seasonality (hourly data), s=7 for weekly (daily data)
- Higher AIC indicates worse fit - try different parameters to minimize AIC
""")

# Price area selector
chosen_area, city_info = choose_price_area(show_selector=True)
lat, lon = city_info['Latitude'], city_info['Longitude']
city_name = city_info['City']

st.markdown(f"**Selected area:** {chosen_area} ({city_name})")
st.markdown("---")

# Helper to format large energy values into kWh/MWh/GWh/TWh per day
def format_energy_value(v: float) -> str:
    abs_v = abs(v)
    if abs_v < 1_000:  # < 1 thousand kWh
        return f"{v:,.2f} kWh/day"
    if abs_v < 1_000_000:  # < 1 million kWh
        return f"{v/1_000:,.2f} MWh/day"
    if abs_v < 1_000_000_000:  # < 1 billion kWh
        return f"{v/1_000_000:,.2f} GWh/day"
    return f"{v/1_000_000_000:,.2f} TWh/day"

# Configuration section
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Energy Variable**")
    energy_type = st.selectbox("Type", ["Production", "Consumption"])
    if energy_type == "Production":
        energy_group = st.selectbox("Group", ["wind", "solar", "hydro", "thermal", "other", "Total"])
    else:
        energy_group = st.selectbox("Group", ["Total"])

with col2:
    st.markdown("**Time Period**")
    start_date = st.date_input("Start Date", value=datetime(2022, 1, 1), min_value=datetime(2018,1,1), max_value=datetime.today())
    end_date = st.date_input("End Date", value=datetime(2023, 12, 31), min_value=start_date, max_value=datetime.today())

st.markdown("---")    
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Confidence Interval**")
    conf_level = st.slider("Confidence Interval (%)", 80, 99, 95)
with col2:
    st.markdown("**Forecast Horizon**")
    forecast_horizon = st.slider("Forecast (days)", min_value=7, max_value=90, value=30)
with col3:
    st.markdown("**Exogenous Variables**")
    use_exog = st.checkbox("Use weather data")
    exog_vars = []
    if use_exog:
        exog_vars = st.multiselect(
            "Select variables",
            ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"],
            default=["temperature_2m"])

st.markdown("---")
st.markdown("**SARIMAX Parameters**")
st.markdown(""")
### Parameter Guide
- **p, d, q**: Non-seasonal AR, differencing, MA orders
- **P, D, Q**: Seasonal AR, differencing, MA orders  
- **s**: Seasonal period in **days** (data is daily). Use 7 for weekly, 365 for yearly (slow!), or 0 for none
- **Exogenous variables**: External factors (weather) that may influence energy
""")
col1, col2 = st.columns(2)
# dividing non-seasonal and seasonal parameters with default vaules
with col1:
    st.markdown("*Non-seasonal (p,d,q)*")
    subcol1, subcol2, subcol3 = st.columns(3)
    with subcol1:
        p = st.text_input("p (lags)", value="1", key="p_input", help="AutoRegressive order: how many past values to use (0-3 typical)")
        p = int(p) if p.isdigit() else 1
    with subcol2:
        d = st.text_input("d (diff)", value="1", key="d_input", help="Differencing order: 0=stationary, 1=trending, 2=accelerating (0-2 typical)")
        d = int(d) if d.isdigit() else 1
    with subcol3:
        q = st.text_input("q (errors)", value="1", key="q_input", help="Moving Average order: how many past errors to use (0-3 typical)")
        q = int(q) if q.isdigit() else 1

with col2:
    st.markdown("*Seasonal (P,D,Q,s)*")
    subcol1, subcol2, subcol3, subcol4 = st.columns(4)
    with subcol1:
        P = st.text_input("P (seas. lags)", value="1", key="P_input", help="Seasonal AR order: seasonal past values (0-2 typical)")
        P = int(P) if P.isdigit() else 1
    with subcol2:
        D = st.text_input("D (seas. diff)", value="0", key="D_input", help="Seasonal differencing: removes seasonal trend (usually 0 or 1)")
        D = int(D) if D.isdigit() else 0
    with subcol3:
        Q = st.text_input("Q (seas. errors)", value="1", key="Q_input", help="Seasonal MA order: seasonal past errors (0-2 typical)")
        Q = int(Q) if Q.isdigit() else 1
    with subcol4:
        s = st.text_input("s (days)", value="7", key="s_input", help="Seasonal period in days: 7=weekly, 365=yearly, 0=none")
        s = int(s) if s.isdigit() else 7

st.markdown("---")

# Run forecast button
if st.button("Run Forecast", type="primary"):
    with st.spinner("Loading and preparing data..."):
        # Load energy data
        if energy_type == "Production":
            energy_df = load_energy_data_v2()
            group_col = 'productiongroup'
        else:
            energy_df = load_consumption_data()
            group_col = 'consumptiongroup'
        
        # Filter by area
        energy_df = energy_df[energy_df['area'] == chosen_area].copy()
        
        # Filter by group
        if energy_group != "Total":
            energy_df = energy_df[energy_df[group_col] == energy_group].copy()
        
        # Convert to datetime and filter date range
        energy_df['starttime'] = pd.to_datetime(energy_df['starttime'])
        energy_df = energy_df[
            (energy_df['starttime'] >= pd.Timestamp(start_date)) &
            (energy_df['starttime'] <= pd.Timestamp(end_date))
        ].copy()
        
        # Aggregate to hourly
        energy_series = energy_df.groupby('starttime')['quantitykwh'].sum().sort_index()
        
        if len(energy_series) < 24:
            st.error("Not enough data for the selected period. Please adjust your filters.")
            st.stop()
        
        # Resample to daily for better performance
        energy_daily = energy_series.resample('D').sum()
        
        # Scale energy data to prevent numerical instability (divide by 1 million)
        energy_scale_factor = 1_000_000  # Convert to MWh (mega-scale)
        energy_daily_scaled = energy_daily / energy_scale_factor
        
        # Load exogenous variables if selected
        exog_train = None
        exog_forecast = None
        
        if use_exog and len(exog_vars) > 0:
            # Determine years needed
            years_needed = list(range(start_date.year, end_date.year + 2))
            weather_df = get_weather_data(lat, lon, years_needed)
            
            # Filter to training period
            weather_train = weather_df[
                (weather_df.index >= pd.Timestamp(start_date)) &
                (weather_df.index <= pd.Timestamp(end_date))
            ][exog_vars].copy()
            
            # Resample to daily
            weather_train_daily = weather_train.resample('D').mean()
            
            # Align with energy data
            exog_train = weather_train_daily.reindex(energy_daily.index).fillna(method='ffill')
            
            # Standardize exogenous variables to prevent numerical issues such as singular matrix errors
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            exog_train_scaled = pd.DataFrame(
                scaler.fit_transform(exog_train),
                index=exog_train.index,
                columns=exog_train.columns
            )
            
            # Prepare forecast period exogenous data
            forecast_start = energy_daily.index[-1] + timedelta(days=1)
            forecast_end = forecast_start + timedelta(days=forecast_horizon - 1)
            
            weather_forecast = weather_df[
                (weather_df.index >= forecast_start) &
                (weather_df.index <= forecast_end)
            ][exog_vars].copy()
            
            exog_forecast = weather_forecast.resample('D').mean()
            
            # If we don't have future weather data, use last known values
            if len(exog_forecast) < forecast_horizon:
                st.warning("Future weather data not available. Using last known values for forecast.")
                last_values = weather_train_daily.iloc[-1]
                forecast_dates = pd.date_range(forecast_start, periods=forecast_horizon, freq='D')
                exog_forecast = pd.DataFrame(
                    [last_values.values] * forecast_horizon,
                    index=forecast_dates,
                    columns=exog_vars
                )
            
            # Standardize forecast exogenous variables using same scaler
            exog_forecast_scaled = pd.DataFrame(
                scaler.transform(exog_forecast),
                index=exog_forecast.index,
                columns=exog_forecast.columns
            )
    
    with st.spinner("Training SARIMAX model..."):
        try:
            # Use scaled exogenous variables if available
            exog_train_final = exog_train_scaled if use_exog and len(exog_vars) > 0 else None
            
            # Fit SARIMAX model on SCALED energy data
            model = SARIMAX(
                energy_daily_scaled,
                exog=exog_train_final,
                order=(p, d, q),
                seasonal_order=(P, D, Q, s),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            results = model.fit(disp=False, maxiter=200)
            
            # Check for convergence warnings
            if hasattr(results, 'mle_retvals') and results.mle_retvals is not None:
                if results.mle_retvals.get('warnflag', 0) != 0:
                    st.warning("⚠️ Model convergence issue detected. Consider simplifying parameters or checking data quality.")
            
            # Generate forecast
            if exog_train_final is not None:
                forecast = results.get_forecast(steps=forecast_horizon, exog=exog_forecast_scaled)
            else:
                forecast = results.get_forecast(steps=forecast_horizon)
            
            # Rescale forecast back to original kWh units
            forecast_mean = forecast.predicted_mean * energy_scale_factor
            forecast_ci = forecast.conf_int(alpha=1 - conf_level/100) * energy_scale_factor
            
            # Create forecast dates
            forecast_dates = pd.date_range(
                start=energy_daily.index[-1] + timedelta(days=1),
                periods=forecast_horizon,
                freq='D'
            )
            
            st.success("Model trained successfully!")
            
            # Display model summary in code block for better formatting
            with st.expander("Model Summary"):
                st.code(str(results.summary()), language=None)
            
            # Plot results
            st.subheader("Forecast Results")
            
            fig = go.Figure()
            
            # Historical data (unscaled for display)
            fig.add_trace(go.Scatter(
                x=energy_daily.index,
                y=energy_daily.values,
                mode='lines',
                name='Historical',
                line=dict(color='steelblue', width=2)
            ))
            
            # Forecast
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_mean.values,
                mode='lines',
                name='Forecast',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_ci.iloc[:, 0].values,
                mode='lines',
                name=f'{conf_level}% CI Lower',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_ci.iloc[:, 1].values,
                mode='lines',
                name=f'{conf_level}% CI Upper',
                line=dict(width=0),
                fillcolor='rgba(255, 0, 0, 0.2)',
                fill='tonexty',
                showlegend=True
            ))
            
            # Add vertical line at forecast start
            fig.add_vline(
                x=energy_daily.index[-1].timestamp() * 1000,
                line_dash="dot",
                line_color="gray",
                annotation_text="Forecast Start"
            )
            
            fig.update_layout(
                title=f"{energy_type} Forecast: {energy_group} in {chosen_area}",
                xaxis_title="Date",
                yaxis_title="Energy (kWh/day)",
                height=600,
                hovermode='x unified',
                legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast statistics
            st.subheader("Forecast Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean Forecast", format_energy_value(forecast_mean.mean()))
            with col2:
                st.metric("Max Forecast", format_energy_value(forecast_mean.max()))
            with col3:
                st.metric("Min Forecast", format_energy_value(forecast_mean.min()))
            with col4:
                st.metric("AIC", f"{results.aic:.2f}")
            st.caption("Values auto-scaled (kWh → MWh → GWh → TWh).")
            
            # Residual diagnostics
            with st.expander("Residual Diagnostics"):
                residuals = results.resid
                
                fig_resid = go.Figure()
                fig_resid.add_trace(go.Scatter(
                    x=energy_daily.index,
                    y=residuals,
                    mode='lines',
                    name='Residuals',
                    line=dict(color='purple')
                ))
                fig_resid.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_resid.update_layout(
                    title="Model Residuals",
                    xaxis_title="Date",
                    yaxis_title="Residual",
                    height=400
                )
                st.plotly_chart(fig_resid, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Mean Residual", f"{residuals.mean():.2f}")
                with col2:
                    st.metric("Std Residual", f"{residuals.std():.2f}")
            
        except Exception as e:
            st.error(f"Error during model training: {str(e)}")
            st.info("""**Troubleshooting tips:**
            - Reduce model complexity: Try (1,1,1)(0,0,0,0) first, then add seasonal components
            - Use fewer exogenous variables (1-2 maximum) or disable them
            - Ensure you have enough data: at least 2-3 seasonal cycles (48-72 days for s=24)
            - Check for missing values or extreme outliers in your data
            - Lower seasonal period s if using small datasets (e.g., s=7 instead of s=24)
            """)

st.markdown("---")
