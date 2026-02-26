import streamlit as st
from pymongo.mongo_client import MongoClient

# Hent Mongo URI fra st.secrets eller miljøvariabler

def get_mongo_uri():
    usr = st.secrets["mongo"]["username"]
    pwd = st.secrets["mongo"]["password"]
    cluster = st.secrets["mongo"]["cluster"]
    return f"mongodb+srv://{usr}:{pwd}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Returnerer cached MongoClient
@st.cache_resource
def get_client():
    uri = get_mongo_uri()
    return MongoClient(uri)
