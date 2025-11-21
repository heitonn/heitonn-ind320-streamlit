import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

    # Plotly pie chart
    fig = px.pie(
        group_sum,
        values='quantitykwh',
        names='productiongroup',
        title=f"Total Production by Group in {chosen_area} (2021)",
        hole=0.3  # Makes it a donut chart for better readability
    )
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Production: %{value:,.0f} kWh<br>Percentage: %{percent}<extra></extra>'
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.05),
        height=500,
        margin=dict(l=20, r=150, t=60, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

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

    # Choosing month and year
    col_month, col_year = st.columns(2)
    with col_month:
        months = df['month'].unique().tolist()
        chosen_month = st.selectbox("Velg måned:", months)
    with col_year:
        years = sorted(df['year'].unique().tolist())
        chosen_year = st.selectbox("Velg år:", years)

    # Filtering data 
    df_filtered = df[
        (df['area'] == chosen_area) &
        (df['productiongroup'].isin(selected_groups)) &
        (df['month'] == chosen_month) &
        (df['year'] == chosen_year)
    ]

    # Plotly line plot
    if not df_filtered.empty:
        df_filtered_sorted = df_filtered.sort_values('starttime')
        
        fig = px.line(
            df_filtered_sorted,
            x='starttime',
            y='quantitykwh',
            color='productiongroup',
            markers=True,
            title=f"Produksjon i {chosen_area} - {chosen_month} {chosen_year}",
            labels={'starttime': 'Dato', 'quantitykwh': 'Produksjon (kWh)', 'productiongroup': 'Production Group'}
        )
        fig.update_traces(
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d %H:%M}<br>Production: %{y:,.0f} kWh<extra></extra>'
        )
        fig.update_layout(
            xaxis=dict(tickangle=45),
            height=500,
            margin=dict(l=40, r=40, t=60, b=100),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
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
