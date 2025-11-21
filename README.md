# heitonn-ind320-streamlit
Public repository for project work in IND320.

## mapstructure of the streamlit app 
my_streamlit_app/
    .streamlit/
        secrets.toml
    open-meteo-subset.csv
    requirements.txt
    Streamlit_app.py
    pages/
        02_Energy_Data.py
        03_Energy_Decomposition.py
        04_Weather_January_Overview.py
        05_Weather_Visualizer.py
        06_Weather_anomalies.py
        07_empty.py
    utils/
        constants.py
        load_energy_data.py
        ui_helpers.py
        weather_data_fetcher.py
        __pycache__/
    .cache.sqlite


## Assignment 1
- Reading and plotting weather data from CSV files.
- Creating streamlit app to visualize weather data. 

## Assignment 2
- Fetching energy data using the [Elhub API](https://api.elhub.no/energy-data-api).  
- Reading data into Cassandra with Spark.  
- Reading data into MongoDB using Spark.  
- Plotting data and updating a Streamlit app to visualize energy production.

## Assignment 3
- Fetching historical weather data from open meteo API
- Using DCT to create seasonally adjusted temperature data 
- Using LOF to find anomalies in percipitation data 
- Creating spectogram and STL for energy production data (used in assignment 2)
- Updating Streamlit app with two new pages 

## Notes
- Streamlit app uses secrets for MongoDB connection (managed via Streamlit Cloud Secrets).  
- Requirements are listed in `requirements.txt`.
