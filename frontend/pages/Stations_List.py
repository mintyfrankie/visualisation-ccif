import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Climate Change in France", page_icon="🌍", layout="wide")
conn = sqlite3.connect("./data/data.db")


@st.cache_data
def load_stations() -> pd.DataFrame:
    """
    Load stations metadata from the database.

    Returns:
        DataFrame: A pandas DataFrame containing the stations data.
    """

    query = """
    SELECT *
    FROM stations
    WHERE station_id IN (
        SELECT DISTINCT station_id
        FROM measurements
        )
    """
    df = pd.read_sql(query, conn, index_col="id")

    df["station_id"] = df["station_id"].astype(str)
    return df


def display_page():
    """
    Main function to display the page.
    """

    st.write("# Station List")
    st.write("""
    **This page displays a list of all the weather stations included in the dataset.**
    """)

    stations = load_stations()

    with st.container(border=False):
        st.map(
            stations,
            latitude="latitude",
            longitude="longitude",
            color="#576B6B",
            zoom=4,
            size=0.1,
            use_container_width=True,
        )

    st.dataframe(
        stations,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "station_id",
            "name",
            "department_id",
            "city",
            "latitude",
            "longitude",
            "altitude",
        ],
        column_config={
            v: v.replace("_", " ").capitalize().replace("id", "ID")
            for v in stations.columns
        },
    )


###
display_page()
