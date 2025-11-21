# utils/ui_helpers.py
import streamlit as st
from utils.constants import city_data_df

# st.radio buttons, with labels: price area and city 
# used on all pages 
# horizontal layout
# Now also respects session_state from map selection
def choose_price_area(show_selector=True):
    """
    Choose a price area either from session state (map selection) or radio buttons.
    
    Args:
        show_selector (bool): If True, shows radio buttons. If False, only uses session state.
    
    Returns:
        tuple: (chosen_area, row) where row is the city_data_df row for that area
    """
    available_areas = city_data_df["PriceArea"].tolist()
    
    # Check if area was selected via map (session state)
    if "chosen_area" in st.session_state:
        chosen_area = st.session_state["chosen_area"]
    else:
        # Default to first area if not set
        chosen_area = available_areas[0]
        st.session_state["chosen_area"] = chosen_area
    
    # Show radio buttons if requested (for pages that want manual selection)
    if show_selector:
        labels = [f"{area} – {city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]}" for area in available_areas]
        label_to_area = {label: area for label, area in zip(labels, available_areas)} 
        
        # Find current label
        current_label = None
        for label, area in label_to_area.items():
            if area == chosen_area:
                current_label = label
                break
        
        # Show selector with current selection
        selected_label = st.radio(
            "Select price area:", 
            labels,
            index=labels.index(current_label) if current_label in labels else 0,
            horizontal=True,
            key="price_area_radio"
        )
        
        # Update session state if selection changed
        new_area = label_to_area[selected_label]
        if new_area != chosen_area:
            st.session_state["chosen_area"] = new_area
            chosen_area = new_area
    
    # Get the row data
    row = city_data_df[city_data_df["PriceArea"] == chosen_area].iloc[0]

    return chosen_area, row