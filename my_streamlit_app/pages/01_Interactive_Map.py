import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
from datetime import datetime, timedelta

# imports from utils
from utils.constants import city_data_df
from utils.load_energy_data import load_energy_data_v2, load_consumption_data

# Page config
st.set_page_config(page_title="Interactive Map", layout="wide", page_icon="🗺️")
st.title("🗺️ Interactive Energy Map")
st.markdown("Explore energy production and consumption across Norwegian price areas. Click on cities to select a region for detailed analysis.")

# Load GeoJSON file for Norwegian price areas
@st.cache_data
def load_geojson():
    try:
        with open("file.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        return geojson_data
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

geojson_data = load_geojson()

# Load energy data
production_df = load_energy_data_v2()
consumption_df = None
try:
    consumption_df = load_consumption_data()
except Exception as e:
    st.warning("Consumption data not available. Only production data will be shown.")

# Initialize session state
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

if "chosen_area" not in st.session_state:
    st.session_state["chosen_area"] = "NO1"  # Default

# Get current chosen area from session state
chosen_area = st.session_state.get("chosen_area", "NO1")

# Settings for data type, group, days
col_settings1, col_settings2, col_settings3 = st.columns([2, 2, 1])

with col_settings1:
    # Only show data types that are available
    available_data_types = ["Production"]
    if consumption_df is not None:
        available_data_types.append("Consumption")
    
    data_type = st.selectbox(
        "Data Type:",
        available_data_types,
        key="data_type",
        label_visibility="collapsed",
        help="Select Production or Consumption data"
    )

# Select the appropriate dataframe based on data type
if data_type == "Production":
    df = production_df
else:
    df = consumption_df if consumption_df is not None else production_df

with col_settings2:
    # Get available production/consumption groups based on selected data type
    if data_type == "Production":
        available_groups = df['productiongroup'].unique().tolist()
        selected_group = st.selectbox(
            "Group:", 
            available_groups, 
            key="prod_group",
            label_visibility="collapsed",
            help="Select energy production group"
        )
    else:
        # Consumption groups
        if 'consumptiongroup' in df.columns:
            available_groups = df['consumptiongroup'].unique().tolist()
            selected_group = st.selectbox(
                "Group:", 
                available_groups, 
                key="cons_group",
                label_visibility="collapsed",
                help="Select consumption group"
            )
        else:
            selected_group = "Total"

with col_settings3:
    days = st.slider(
        "Days:", 
        1, 7, 30,
        key="days",
        label_visibility="collapsed",
        help="Time interval in days"
    )

# Calculate mean values per area for choropleth
end_date = df['starttime'].max()
start_date = end_date - timedelta(days=days)

# Show the actual date range being displayed
st.caption(f"📅 Data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

df_filtered = df[(df['starttime'] >= start_date) & (df['starttime'] <= end_date)]

# Filter by group if not "Total"
if data_type == "Production" and selected_group != "Total":
    df_filtered = df_filtered[df_filtered['productiongroup'] == selected_group]
elif data_type == "Consumption" and selected_group != "Total":
    if 'consumptiongroup' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['consumptiongroup'] == selected_group]

# Calculate area statistics
area_stats = df_filtered.groupby('area')['quantitykwh'].agg(['mean', 'sum', 'max']).reset_index()
area_stats.columns = ['area', 'mean_kwh', 'total_kwh', 'peak_kwh']
area_means = area_stats.set_index('area')['mean_kwh'].to_dict()

# Price area selection
available_areas = ["NO1", "NO2", "NO3", "NO4", "NO5"]

cols = st.columns(5)
for idx, area in enumerate(available_areas):
    with cols[idx]:
        # Get city name for this area from city_data_df in utils/constants.py
        city_name = city_data_df[city_data_df['PriceArea'] == area]['City'].values[0]
        area_value = area_means.get(area, 0)
        
        # display value energy data 
        if area_value == 0: # no data for area
            value_display = "0 kWh"
        elif area_value < 1000:
            value_display = f"{area_value:.0f} kWh" # show actual value
        else:
            value_display = f"{area_value/1000:.1f}k kWh" # show in 'k kWh' format
        
        # display button with selected area highlighted
        #selected area bolded
        if area == chosen_area:
            button_label = f"**{city_name}**\n{value_display}" # displays selected area 
            button_type = "primary"
        # not selected area no bolded
        else:
            button_label = f"{city_name}\n{value_display}"
            button_type = "secondary"
        
        # display button
        if st.button(
            button_label, 
            key=f"btn_{area}",
            use_container_width=True,
            type=button_type,
            help=f"Select {area} - {city_name}",
            disabled=(area == chosen_area)
        ):
            st.session_state["chosen_area"] = area
            st.rerun()

st.divider()

# MAIN LAYOUT: MAP (LEFT) + INFO (RIGHT) 
if geojson_data:
    col_map, col_info = st.columns([2, 1])

    with col_map:
        # Prepare data for choropleth
        map_data = pd.DataFrame([
            {"area": area, "mean_kwh": area_means.get(area, 0)}
            for area in available_areas
        ])
        
        # Add space to match GeoJSON format ("NO1" -> "NO 1")
        map_data['area_display'] = map_data['area'].str.replace('NO', 'NO ')
        
        # Create choropleth map using plotly express
        fig = px.choropleth_mapbox(
            map_data,
            geojson=geojson_data,
            locations='area_display',
            featureidkey="properties.ElSpotOmr",
            color='mean_kwh',
            # colorscale to illustrate energy levels
            color_continuous_scale=[
                [0, "rgb(200, 200, 255)"],    # Very light blue for low/zero
                [0.5, "rgb(150, 100, 200)"],  # Purple for medium
                [1, "rgb(255, 100, 100)"]     # Red for high
            ],
            mapbox_style="carto-positron",
            center={"lat": 65, "lon": 15},
            zoom=3.5, #zoom level mapped to norway 
            opacity=0.6,
            labels={'mean_kwh': 'Mean Energy (kWh)'},
            hover_name='area',
            hover_data={'area_display': False, 'mean_kwh': ':.0f'}
        )
        
        # Add black border for selected area only
        for feature in geojson_data.get("features", []):
            properties = feature.get("properties", {})
            raw_name = properties.get("ElSpotOmr", "")
            area_name = raw_name.replace(" ", "") if raw_name else "Unknown"
            
            # Only draw border for selected area
            if area_name == chosen_area:
                geometry = feature.get("geometry", {})
                geometry_type = geometry.get("type", "")
                coordinates = geometry.get("coordinates", [])
                
                if geometry_type == "Polygon":
                    for polygon in coordinates:
                        lons = [coord[0] for coord in polygon]
                        lats = [coord[1] for coord in polygon]
                        
                        fig.add_trace(go.Scattermapbox(
                            lon=lons,
                            lat=lats,
                            mode='lines',
                            line=dict(width=4, color='black'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                
                elif geometry_type == "MultiPolygon":
                    for multi_polygon in coordinates:
                        for polygon in multi_polygon:
                            lons = [coord[0] for coord in polygon]
                            lats = [coord[1] for coord in polygon]
                            
                            fig.add_trace(go.Scattermapbox(
                                lon=lons,
                                lat=lats,
                                mode='lines',
                                line=dict(width=4, color='black'),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
        
        # Add city markers
        for _, row in city_data_df.iterrows():
            is_selected = row['PriceArea'] == chosen_area
            fig.add_trace(go.Scattermapbox(
                lon=[row['Longitude']],
                lat=[row['Latitude']],
                mode='markers+text',
                marker=dict(
                    size=12 if is_selected else 8,
                    color='red' if is_selected else 'darkblue'
                ),
                text=row['City'],
                textfont=dict(size=10, color='black'),
                name=f"{row['PriceArea']} - {row['City']}",
                showlegend=False,
                hovertemplate=f"<b>{row['City']}</b><br>{row['PriceArea']}<extra></extra>"
            ))
        
        # Update layout
        fig.update_layout(
            height=550,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False
        )
        
        # Display the map
        st.plotly_chart(fig, use_container_width=True, key="price_area_map")

    # RIGHT SIDE: INFORMATION PANEL 
    with col_info:
        # Show selected area and city
        city_info = city_data_df[city_data_df['PriceArea'] == chosen_area].iloc[0]
        st.markdown(f"### 📍 {chosen_area}, {city_info['City']}")
    
        
        # Show current settings
        st.markdown("##### Current View")
        st.markdown(f"""
        - **Type:** {data_type}
        - **Group:** {selected_group}
        - **Period:** Last {days} days
        """)
        
        st.divider()
        
        # Show statistics for selected area
        st.markdown("##### Statistics")
        
        selected_area_data = df_filtered[df_filtered['area'] == chosen_area]
        
        if not selected_area_data.empty:
            mean_val = selected_area_data['quantitykwh'].mean()
            total_val = selected_area_data['quantitykwh'].sum()
            peak_val = selected_area_data['quantitykwh'].max()
        else:
            mean_val = total_val = peak_val = 0
        
        st.markdown(f"""
        - **Mean:** {mean_val:,.0f} kWh
        - **Total:** {total_val/1000:,.0f}k kWh
        - **Peak:** {peak_val:,.0f} kWh
        """)
        
        st.divider()
        
        # Map legend
        st.markdown("##### Map Legend")
        st.markdown("""
        - **Black border** = Selected area
        - **Color scale**:
          - 🔵 Light blue = Low/zero
          - 🟣 Purple = Medium  
          - 🔴 Red = High
        - **Red marker** = Selected city
        - **Blue markers** = Other cities
        """)

    # BOTTOM: ADDITIONAL INFO (IF NEEDED) 
    with st.expander("ℹAbout This Page"):
        st.markdown("""
        This interactive map shows Norwegian electricity price areas (NO1-NO5) with energy data from 2021-2024.
        
        **How to use:**
        - Click city buttons to switch between areas
        - Adjust settings to view different data
        - Selected area syncs across all pages
        
        **Note:** The data shown is historical data from the specified date range, not real-time data.
        
        **Data source:** Elhub (via MongoDB)
        """)

else:
    st.error("⚠️ Could not load GeoJSON file!")
    st.warning("""
    ### GeoJSON file missing
    
    Make sure `file.geojson` is in the app folder with valid ElSpot area data.
    """)
