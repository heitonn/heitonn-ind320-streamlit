# heitonn-ind320-streamlit
Public repository for project work in IND320.

**Deployed Streamlit App:** https://heitonn-ind320-app-djubejzwip5rtzkik5276s.streamlit.app/

## Structure of the Streamlit App
```
my_streamlit_app/
    .streamlit/
        secrets.toml
    Energy_Dashboard.py          # Landing page with navigation
    file.geojson                 # Norwegian price area boundaries
    requirements.txt
    pages/
        01_Explore_Map.py        # Interactive GeoJSON map with area selection
        02_Explore_Energy.py     # Energy production overview
        03_Explore_Weather.py    # Weather data visualization
        04_Analyze_Energy_Decomposition.py  # STL decomposition & spectrogram
        05_Analyze_Weather_Anomalies.py     # Temperature SPC & precipitation LOF
        06_Analyze_Snow_Drift.py            # Snow drift calculation (Tabler 2003)
        07_Analyze_Correlations.py          # Sliding window weather-energy correlation
        08_Predict_Energy_Forecast.py       # SARIMAX forecasting with exogenous variables
    utils/
        constants.py             # City coordinates and area definitions
        load_energy_data.py      # MongoDB data loading functions
        snowdrift_calculations.py # Tabler (2003) snow drift algorithm
        ui_helpers.py
        weather_data_fetcher.py  # Open-Meteo API integration
```

## Assignment 1
- Reading and plotting weather data from CSV files.
- Creating Streamlit app to visualize weather data. 

## Assignment 2
- Fetching energy data using the [Elhub API](https://api.elhub.no/energy-data-api).  
- Storing data in Cassandra using PySpark with proper schema definitions.
- Storing data in MongoDB Atlas with duplicate prevention.
- Plotting data and updating Streamlit app to visualize energy production.

## Assignment 3
- Fetching historical weather data from Open-Meteo Archive API.
- Using DCT high-pass filtering to create Seasonally Adjusted Temperature Variations (SATV).
- Detecting temperature outliers using robust statistics (MAD-based SPC boundaries).
- Using Local Outlier Factor (LOF) to detect precipitation anomalies.
- Creating spectrogram and STL decomposition for energy production data.
- Updating Streamlit app with interactive weather anomaly detection and energy decomposition pages.

## Assignment 4
### Streamlit App Refactoring
- **Plotly Integration:** Converted all matplotlib/seaborn plots to interactive Plotly visualizations.
- **Logical Page Structure:** Reorganized pages into task-based categories:
  - **Explore** (Map, Energy, Weather)
  - **Analyze** (Decomposition, Anomalies, Snow Drift, Correlations)
  - **Predict** (SARIMAX Forecasting)
- **Landing Page:** Created Energy_Dashboard.py with navigation to three main sections.

### New Features
- **Interactive Map:** GeoJSON-based choropleth map of Norwegian price areas (NO1-NO5) with:
  - Area selection via buttons (synchronized with session state)
  - Color-coded by energy metrics
  - City markers with coordinates
- **Snow Drift Analysis:** Tabler (2003) snow transport calculation with:
  - Multi-year weather data from Open-Meteo API
  - 16-sector wind rose visualization
  - Configurable parameters (T, F, θ)
  - Fence height recommendations
- **Sliding Window Correlation:** Weather-energy correlation analysis with:
  - Configurable lag, window size, and resolution (hourly/daily/weekly)
  - Energy types: Wind, Solar, Hydro, Thermal production + all consumption groups
  - Weather variables: Temperature, precipitation, wind speed, solar radiation
  - Interactive Plotly plots with normalized scales
- **SARIMAX Forecasting:** Statistical forecasting with:
  - Full parameter control (p,d,q,P,D,Q,s)
  - Exogenous weather variables (temperature, precipitation, wind, solar)
  - Confidence intervals and forecast horizon selection
  - Residual diagnostics (histogram, Q-Q plot, ACF)
  - Model summary with parameter significance tests

### Data Pipeline
- **Elhub API:** Retrieved hourly production and consumption data (2021-2024) for all price areas.
- **Cassandra:** Stored production and consumption data in separate tables using PySpark.
- **MongoDB Atlas:** Migrated to new database structure with production and consumption collections.
- **Open-Meteo API:** Multi-year weather data retrieval with caching and error handling.

### Bonus Features Implemented
- **Progress Indicators:** Spinners and caching throughout the app for better UX.
- **Error Handling:** Graceful handling of missing data, API errors, and NaN values.
- **Weather as Exogenous Variables:** Full integration in SARIMAX forecasting page.

### Extreme Weather Analysis
Documented correlation patterns during:
- **Storm Malik (January 2022):** Wind turbine cut-off behavior during extreme winds.
- **Heatwave (May 2024):** Solar production vs. temperature correlation analysis.
- **Cold Snap (December 2023):** Household consumption and thermal production response.
- **Extreme Weather Hans (August 2023):** Hydro production lag after heavy rainfall.

## Technical Stack
- **Frontend:** Streamlit with Plotly for interactive visualizations
- **Data Storage:** MongoDB Atlas, Apache Cassandra
- **Data Processing:** PySpark, pandas, numpy
- **APIs:** Elhub Energy Data API, Open-Meteo Archive API
- **Analysis:** statsmodels (SARIMAX, STL), scipy (DCT, spectrogram), scikit-learn (LOF, scaling)

## Notes
- Streamlit app uses secrets for MongoDB connection (managed via Streamlit Cloud Secrets).
- Requirements are listed in `requirements.txt`.
- GeoJSON data sourced from NVE (Norwegian Water Resources and Energy Directorate).
