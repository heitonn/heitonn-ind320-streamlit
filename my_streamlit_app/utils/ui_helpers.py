# utils/ui_helpers.py
import streamlit as st
from utils.constants import city_data_df

# st.radio buttons, with labels: price area and city 
# used on all pages 
# horizontal layout
def choose_price_area():
    available_areas = city_data_df["PriceArea"].tolist() # finding price areas in city_data_df (from utils/constans)
    labels = [f"{area} – {city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]}" for area in available_areas]
    label_to_area = {label: area for label, area in zip(labels, available_areas)} 
    
    selected_label = st.radio("Select price area:", 
                              labels,  
                              horizontal=True,
                              key="price_area_radio"
                              )
    chosen_area = label_to_area[selected_label]
    st.session_state["chosen_area"] = chosen_area  # store in session state
    row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]

    return chosen_area, row