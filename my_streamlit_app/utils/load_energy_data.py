import pandas as pd
from pymongo.mongo_client import MongoClient
import streamlit as st

def load_energy_data():
    # Mongo connection
    usr = st.secrets["mongo"]["username"]
    pwd = st.secrets["mongo"]["password"]
    cluster = st.secrets["mongo"]["cluster"]
    uri = f"mongodb+srv://{usr}:{pwd}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    @st.cache_data
    def _load():
        client = MongoClient(uri)
        db = client["energy_database"]
        collection = db["energy_collection"]
        data = list(collection.find())
        client.close()
        df = pd.DataFrame(data)
        df['starttime'] = pd.to_datetime(df['starttime'])
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])
        df['month'] = df['starttime'].dt.month_name()
        return df

    return _load()
