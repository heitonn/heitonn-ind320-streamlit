import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo.mongo_client import MongoClient

# imports from utils
from utils.ui_helpers import choose_price_area
from utils.load_energy_data import load_energy_data_v2

# Title and wide layout
st.set_page_config(page_title="Energy Dashboard", layout="wide")
st.header("Visualizing energy data" )

# loading energy data from mongoDB
df = load_energy_data_v2() # function in utils/load_energy_data.py

# Area selection
chosen_area, row = choose_price_area() # function in utils/ui_helpers.py

# Dividing page in two columns
col1, col2 = st.columns(2, gap="large")

# Column 1: pie chart
with col1:
    st.subheader("Total Production per Group")

    # Filtering and summarizing per production type
    df_area = df[df['area'] == chosen_area]
    group_sum = df_area.groupby('productiongroup')['quantitykwh'].sum().reset_index()
    total = group_sum['quantitykwh'].sum()

    # Pie chart
    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, _ = ax.pie(group_sum['quantitykwh'], labels=None, startangle=90)

    # Legend with percentage
    labels = [f"{grp} ({val/total*100:.1f}%)" for grp, val in zip(group_sum['productiongroup'], group_sum['quantitykwh'])]
    ax.legend(wedges, labels, title="Production Group", loc="center left", bbox_to_anchor=(-0.3, 0.75))
    ax.set_title(f"Total Production by Group in {chosen_area} (2021)")
    st.pyplot(fig)

# Column 2 Line plot 
with col2:
    st.subheader("Production Over Time")

    # Choosing production group with st.pills 
    all_groups = df['productiongroup'].unique().tolist()
    selected_groups = st.pills(
        "Velg produksjonsgruppe(r):",
        options=all_groups,
        selection_mode="multi",
        default=[all_groups[0]]
        )

    # Choosing month 
    months = df['month'].unique().tolist()
    chosen_month = st.selectbox("Velg måned:", months)

    # Filtering data 
    df_filtered = df[
        (df['area'] == chosen_area) &
        (df['productiongroup'].isin(selected_groups)) &
        (df['month'] == chosen_month)
    ]

    # Line plot
    if not df_filtered.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        for group in selected_groups:
            df_group = df_filtered[df_filtered['productiongroup'] == group].sort_values('starttime')
            ax.plot(df_group['starttime'], df_group['quantitykwh'], marker='o', label=group)
        ax.set_xlabel("Dato")
        ax.set_ylabel("Produksjon (kWh)")
        ax.set_title(f"Produksjon i {chosen_area} - {chosen_month}")
        ax.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.write("Ingen data for valgt kombinasjon.")

with st.expander("Data source"):
    st.markdown(
        """
        The presented data on this page is collected from the 
        [**Elhub** database](https://api.elhub.no/energy-data-api).  
        The dataset contains hourly production data from the production groups **solar**, **wind**, **hydro**, **thermal**, and **other**,  
        across the five Norwegian price areas **NO1–NO5**.  
        The numbers represent measured **energy production in kWh per hour**.
        """
        )
