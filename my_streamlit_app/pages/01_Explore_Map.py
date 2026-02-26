import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import os
import json
import pandas as pd
from datetime import timedelta
from utils.constants import city_data_df
from utils.load_energy_data import load_energy_data, load_consumption_data

# Page config
st.set_page_config(page_title="Interactive Map", layout="wide", page_icon="🗺️")
st.title("🗺️ Interactive Energy Map")
st.markdown("Explore energy production and consumption across Norwegian price areas. Click on cities to select a region for detailed analysis.")


# Load GeoJSON file for Norwegian price areas
@st.cache_data
def load_geojson():
    try:
        # Get path relative to this file's parent directory
        base_dir = os.path.dirname(os.path.dirname(__file__))
        geojson_path = os.path.join(base_dir, "assets", "file.geojson")
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        return geojson_data
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None


geojson_data = load_geojson()

# Load energy data
production_df = load_energy_data()
consumption_df = None
try:
    consumption_df = load_consumption_data()
except Exception:
    st.warning("Consumption data not available. Only production data will be shown.")

# Initialize session state
if "chosen_area" not in st.session_state:
    st.session_state["chosen_area"] = "NO1"  # Default

# Get current chosen area from session state
chosen_area = st.session_state.get("chosen_area", "NO1")

# Settings for data type, group, days


# Restore dropdowns for energy type and group at the top
col_type, col_group = st.columns(2)
available_data_types = ["Production"]
if consumption_df is not None:
    available_data_types.append("Consumption")
with col_type:
    data_type = st.selectbox(
        "Energi type:",
        available_data_types,
        key="data_type",
        help="Velg produksjon eller konsum"
    )
    df = production_df.copy() if data_type == "Production" else (consumption_df.copy() if consumption_df is not None else production_df.copy())
    df_grouped = df.copy()
with col_group:
    if data_type == "Production":
        available_groups = df['productiongroup'].unique().tolist()
        selected_group = st.selectbox(
            "Type:", 
            available_groups, 
            key="prod_group",
            help="Velg produksjonsgruppe"
        )
        if selected_group != "Total":
            df_grouped = df[df['productiongroup'] == selected_group]
    else:
        if 'consumptiongroup' in df.columns:
            available_groups = df['consumptiongroup'].unique().tolist()
            selected_group = st.selectbox(
                "Type:", 
                available_groups, 
                key="cons_group",
                help="Velg konsumgruppe"
            )
        if selected_group != "Total":
            df_grouped = df[df['consumptiongroup'] == selected_group]
        else:
            selected_group = "Total"

# Month/year selection in right column
# Filter df by group

# Month/year selection will be handled in col_info, so initialize df_filtered here for area_stats
st.divider()
df_filtered = df_grouped.copy()
# Calculate area statistics for map coloring
area_stats = df_filtered.groupby('area')['quantitykwh'].agg(['mean', 'sum', 'max']).reset_index()
area_stats.columns = ['area', 'mean_kwh', 'total_kwh', 'peak_kwh']
area_means = area_stats.set_index('area')['mean_kwh'].to_dict()

st.divider()

# MAIN LAYOUT: MAP (LEFT) + INFO (RIGHT) 
# LEFT SIDE: MAP
if geojson_data:
    col_map, col_info = st.columns([2, 1])

    with col_map:
        # Prepare data for choropleth
        available_areas = city_data_df["PriceArea"].drop_duplicates().tolist()
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
            zoom=4,  #zoom level mapped to norway 
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
                geometry = feature.get("geometry", {})
                coordinates = geometry.get("coordinates", [])

                # Draw border for each polygon ring
                for polygon in coordinates:
                    lons = [coord[0] for coord in polygon]
                    lats = [coord[1] for coord in polygon]
                    
                    fig.add_trace(go.Scattermapbox(
                        # finding longitudes and latitudes for border
                        lon=lons, 
                        lat=lats,
                        mode='lines',
                        line=dict(width=3, color='black'), #line surrounding selected area
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
        center_lat = city_data_df['Latitude'].mean()
        center_lon = city_data_df['Longitude'].mean()
        center_lat = 65.5 
        center_lon = 15.0
        folium_map = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles="cartodbpositron", zoom_control=False)

        # Legg til GeoJSON med klikkbare områder
        gj = folium.GeoJson(
            geojson_data,
            name="Price Areas",
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.3
            },
            highlight_function=lambda x: {
                'fillColor': '#ffaf00',
                'color': 'red',
                'weight': 3,
                'fillOpacity': 0.5
            },
            tooltip=folium.GeoJsonTooltip(fields=['ElSpotOmr'], aliases=['Area:']),
        )
        gj.add_to(folium_map)

        # Legg til city markers
        for _, row in city_data_df.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"{row['City']} ({row['PriceArea']})",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(folium_map)

        # Vis kart og fang klikk
        map_data = st_folium(folium_map, width=600, height=1000)

        # Oppdater valgt område hvis klikk
        if map_data and map_data.get('last_active_drawing'):
            feature = map_data['last_active_drawing']
            if 'properties' in feature and 'ElSpotOmr' in feature['properties']:
                area_clicked = feature['properties']['ElSpotOmr'].replace(' ', '')
                st.session_state['chosen_area'] = area_clicked
                st.rerun()

    # RIGHT SIDE: INFORMATION PANEL 
    with col_info:
        # Show selected area and city
        city_info = city_data_df[city_data_df['PriceArea'] == chosen_area].iloc[0]
        st.markdown(f"### 📍 {chosen_area}, {city_info['City']}")

        # Month and year selection dropdowns
        st.markdown("##### Velg periode")
        col_month, col_year = st.columns(2)
        months = df_grouped['month'].unique().tolist()
        years = sorted(df_grouped['year'].unique().tolist())
        with col_month:
            chosen_month = st.selectbox("Måned:", months, key="map_month")
        with col_year:
            chosen_year = st.selectbox("År:", years, key="map_year")

        # Show current settings
        st.markdown("##### Gjeldende visning")
        st.markdown(f"""
        - **Type:** {data_type}
        - **Group:** {selected_group}
        - **Period:** {chosen_month} {chosen_year}
        """)

        st.divider()

        # Show statistics for selected area
        st.markdown("##### Statistikker")

        # Filter df_grouped by month/year
        df_filtered = df_grouped[(df_grouped['month'] == chosen_month) & (df_grouped['year'] == chosen_year)]
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


else: # usefull feedback if GeoJSON fails to load
    st.error("⚠️ Could not load GeoJSON file!")
    st.warning("""
    ### GeoJSON file missing
    
    Make sure `file.geojson` is in the app folder with valid ElSpot area data.
    """)
