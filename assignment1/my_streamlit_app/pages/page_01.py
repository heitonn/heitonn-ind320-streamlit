import streamlit as st
import pandas as pd

st.header('Weatherdata January 2020 overview')

st.write("This table shows the first month (January 2020) "
"for each weather variable with mini line charts.")

# Reading csv, converting time 

@st.cache_data
def load_data():
    df = pd.read_csv(r"C:\Users\heito\Documents\IND320\assignment1\my_streamlit_app\open-meteo-subset.csv")
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    return df

df = load_data()


# finding data for january
january = df.loc["2020-01"]  


#Creating a new pandas dataframe containing only values for january 
january_table = pd.DataFrame({
    "Temperature (°C)": [january["temperature_2m (°C)"].values],
    "Precipitation (mm)": [january["precipitation (mm)"].values],
    "Wind speed (m/s)": [january["wind_speed_10m (m/s)"].values],
    "Wind gusts (m/s)": [january["wind_gusts_10m (m/s)"].values],
    "Wind direction (°)": [january["wind_direction_10m (°)"].values],
})

#transposing and setting new index
january_table = january_table.T.reset_index()

#naming columns
january_table.columns = ["Variable", "Values"]

# showing table og lineplots using LineChartColumn 
st.dataframe(
    january_table,
    column_config={
        "Values": st.column_config.LineChartColumn("January"),
    },
    hide_index=True,
)
