import pandas as pd
from pymongo.mongo_client import MongoClient
import streamlit as st


def load_energy_data(area=None, start_date=None, end_date=None):
    """
    Load production data from MongoDB with optional filtering.
    Args:
        area (str): Price area or region to filter.
        start_date (str or pd.Timestamp): Start date for filtering (inclusive).
        end_date (str or pd.Timestamp): End date for filtering (inclusive).
    Returns:
        pd.DataFrame: Filtered production data.
    """
    usr = st.secrets["mongo"]["username"]
    pwd = st.secrets["mongo"]["password"]
    cluster = st.secrets["mongo"]["cluster"]
    uri = f"mongodb+srv://{usr}:{pwd}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    @st.cache_data
    def _load(area, start_date, end_date):
        client = MongoClient(uri)
        db = client["energy_database"]
        collection = db["production_collection"]

        query = {}
        if area:
            query["area"] = area
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = pd.to_datetime(start_date)
            if end_date:
                date_query["$lte"] = pd.to_datetime(end_date)
            query["starttime"] = date_query

        data = list(collection.find(query))
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

    return _load(area, start_date, end_date)


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
