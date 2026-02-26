import pandas as pd
import streamlit as st
from utils.mongo import get_client


@st.cache_data
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
    client = get_client()
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


@st.cache_data
def load_consumption_data():
    """Load consumption data from MongoDB"""
    client = get_client()
    db = client["energy_database"]
    collection = db["consumption_collection"]
    data = list(collection.find())
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
