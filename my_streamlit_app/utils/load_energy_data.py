import pandas as pd
from pymongo.mongo_client import MongoClient
import streamlit as st

def load_energy_data_v2():
    """Load production data from MongoDB"""
    usr = st.secrets["mongo"]["username"]
    pwd = st.secrets["mongo"]["password"]
    cluster = st.secrets["mongo"]["cluster"]
    uri = f"mongodb+srv://{usr}:{pwd}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    @st.cache_data
    def _load(dummy=None):
        client = MongoClient(uri)
        db = client["energy_database"]
        collection = db["production_collection"]
        data = list(collection.find())

        client.close()
        df = pd.DataFrame(data)

        # Clean
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)

        # Ensure starttime exists
        if "starttime" in df.columns:
            df["starttime"] = pd.to_datetime(df["starttime"])
        else:
            raise KeyError(f"Mangler 'starttime'. Kolonner er: {df.columns.tolist()}")

        df["month"] = df["starttime"].dt.month_name()
        df["year"] = df["starttime"].dt.year

        return df

    return _load(dummy = 1) # FORCE CACHE RESET


def load_consumption_data():
    """Load consumption data from MongoDB"""
    usr = st.secrets["mongo"]["username"]
    pwd = st.secrets["mongo"]["password"]
    cluster = st.secrets["mongo"]["cluster"]
    uri = f"mongodb+srv://{usr}:{pwd}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    @st.cache_data
    def _load_consumption(dummy=None):
        client = MongoClient(uri)
        db = client["energy_database"]
        collection = db["consumption_collection"]  # Consumption collection
        data = list(collection.find())

        client.close()
        df = pd.DataFrame(data)

        # Clean
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)

        # Ensure starttime exists
        if "starttime" in df.columns:
            df["starttime"] = pd.to_datetime(df["starttime"])
        else:
            raise KeyError(f"Mangler 'starttime'. Kolonner er: {df.columns.tolist()}")

        df["month"] = df["starttime"].dt.month_name()
        df["year"] = df["starttime"].dt.year

        return df

    return _load_consumption(dummy = 1) # FORCE CACHE RESET
