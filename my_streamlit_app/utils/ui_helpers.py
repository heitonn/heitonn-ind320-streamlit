# utils/ui_helpers.py
import streamlit as st
from utils.constants import city_data_df

def choose_price_area():
    available_areas = city_data_df["PriceArea"].tolist()
    labels = [f"{area} – {city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]}" for area in available_areas]
    label_to_area = {label: area for label, area in zip(labels, available_areas)}

    chosen_area = st.session_state.get("chosen_area", available_areas[0])
    default_label = next((lbl for lbl, area in label_to_area.items() if area == chosen_area), labels[0])

    selected_label = st.radio("Select price area:", labels, index=labels.index(default_label), horizontal=True)
    chosen_area = label_to_area[selected_label]
    st.session_state["chosen_area"] = chosen_area
    row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]

    return chosen_area, row