import streamlit as st
import pandas as pd
from pymongo.mongo_client import MongoClient
import matplotlib.pyplot as plt

st.set_page_config(page_title="Energy Dashboard", layout="wide")

# Del siden i to kolonner
col1, col2 = st.columns(2)
import streamlit as st
from pymongo import MongoClient
import pandas as pd

# Les hemmeligheter fra secrets.toml
usr = st.secrets["mongo"]["username"]
pwd = st.secrets["mongo"]["password"]
cluster = st.secrets["mongo"]["cluster"]

# Sett opp MongoDB URI
uri = f"mongodb+srv://{usr}:{pwd}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Koble til MongoDB
client = MongoClient(uri)
db = client["energy_database"]
collection = db["energy_collection"]

# Hent data
data = list(collection.find())
df = pd.DataFrame(data)
df['starttime'] = pd.to_datetime(df['starttime'])




# Legg inn innhold i kolonne 1
with col1:
    st.subheader("Energy Data from MongoDB")

    if '_id' in df.columns:
        df = df.drop(columns=['_id'])

    # --- 3. Velg område med radio buttons ---
    areas = ['NO1', 'NO2', 'NO3', 'NO4', 'NO5']
    chosen_area = st.radio("Velg price area:", areas)

    # --- 4. Filtrer data for valgt område ---
    df_area = df[df['area'] == chosen_area]

    # --- 5. Grupper og summer per produksjonsgruppe ---
    group_sum = df_area.groupby('productiongroup')['quantitykwh'].sum().reset_index()
    # Beregn total produksjon
    total = group_sum['quantitykwh'].sum()

    
    # --- 6. Lag pie chart med legend ---
    fig, ax = plt.subplots(figsize=(4, 4))

    # Lag pie chart uten tekst og prosent på slices
    wedges, _ = ax.pie(
        group_sum['quantitykwh'],
        labels=None,
        startangle=90)
    
    
    # Lag legend med produksjonsgruppe og prosentandel
    labels = [f"{grp} ({val/total*100:.1f}%)" 
            for grp, val in zip(group_sum['productiongroup'], group_sum['quantitykwh'])]

    ax.legend(wedges, labels, title="Production Group",
            loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    ax.set_title(f"Total Production by Group in {chosen_area} (2021)")
    st.pyplot(fig)



# Legg inn innhold i kolonne 2
with col2:
    st.subheader("Velg produksjonsgrupper og måned")

    df['month'] = df['starttime'].dt.month_name()
    months = df['month'].unique().tolist()
    # Velg produksjonsgrupper (flere kan velges)
    all_groups = df['productiongroup'].unique().tolist()
    selected_groups = st.multiselect("Velg produksjonsgruppe(r):", all_groups, default=[all_groups[0]])

    # Velg måned
    chosen_month = st.selectbox("Velg måned:", months)

    # Filtrer data basert på valgt område, produksjonsgruppe(r) og måned
    df_filtered = df[
        (df['area'] == chosen_area) &
        (df['productiongroup'].isin(selected_groups)) &
        (df['month'] == chosen_month)
    ]

    # Lag line plot hvis det finnes data
    if not df_filtered.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
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