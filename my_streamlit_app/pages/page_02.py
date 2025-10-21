import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os


st.header("Visualizing weather data")
st.write("Select a column and a month range to visualize the data. Use 'All columns' to see everything.")

# Reading data 
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))  # .. går opp en mappe
    csv_path = os.path.join(base_dir, "open-meteo-subset.csv")

    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    return df

df = load_data()

# Choosing column (or all columns)
options = list(df.columns) + ["All columns"]
selected_col = st.selectbox("Select column(s) to plot:", options)

# Sorting data per month 
months = sorted(df.index.to_period("M").unique().strftime("%Y-%m"))
# Selecting month slider
selected_months = st.select_slider(
    "Select months range:",
    options=months,
    value=(months[0], months[0])  # default = first month
)

# Filtering on chosen month
start, end = pd.Period(selected_months[0]), pd.Period(selected_months[1])
mask = (df.index.to_period("M") >= start) & (df.index.to_period("M") <= end)
df_subset = df.loc[mask]

# Plotting 
fig, ax = plt.subplots(figsize=(10,5))
if selected_col == "All columns":
    df_subset.plot(ax=ax)
else:
    df_subset[selected_col].plot(ax=ax)

ax.set_title("Weather data")
ax.set_xlabel("Time")
ax.set_ylabel("Value")
ax.legend(loc="best")

st.pyplot(fig)