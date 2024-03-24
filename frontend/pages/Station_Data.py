import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st
from statsmodels.tsa.seasonal import seasonal_decompose

st.set_page_config(page_title="Climate Change in France", page_icon="🌍", layout="wide")
conn = sqlite3.connect("./data/data.db")


@st.cache_data
def get_station_list():
    query = """
    SELECT station_id
    FROM stations
    WHERE station_id IN (
        SELECT DISTINCT station_id
        FROM measurements
        )
    """
    df = pd.read_sql(query, conn)
    return df


@st.cache_data
def query_station_info(station_id: str):
    query = f"""
        SELECT * FROM stations
        WHERE station_id = "{station_id}"
        """
    df = pd.read_sql(query, conn)
    return df


@st.cache_data
def get_time_series(station_id: str, variable: str):
    query = f"""
        SELECT * FROM measurements
        WHERE station_id = "{station_id}"
        AND variable = "{variable}"
        """
    df = pd.read_sql(query, conn, index_col="id")
    return df


def construct_charts(type: str, station_id: str):
    match type:
        case "temperature":
            tn = get_time_series(station_id, "TN")
            tx = get_time_series(station_id, "TX")
            df = tx.merge(tn, on="timestamp", suffixes=("_max", "_min"))
            min_max_scale = (df["value_min"].min(), df["value_max"].max())
            historical_y = ["value_max", "value_min"]
            decomposition_x = "value_max"
            y_label = "Temperature (°C)"
        case "precipitation":
            df = get_time_series(station_id, "RR")
            min_max_scale = (df["value"].min(), df["value"].max())
            historical_y = ["value"]
            decomposition_x = "value"
            y_label = "Precipitation (mm)"

    st.write(f"## {type.capitalize()}")
    st.write("### Historical Evolution")
    try:
        legend_labels = {
            "value_max": "Max Temperature",
            "value_min": "Min Temperature",
            "value": "Precipitation",
        }

        if df.empty:
            raise ValueError
        st.plotly_chart(
            px.line(
                df,
                x="timestamp",
                y=historical_y,
            )
            .update_yaxes(range=min_max_scale)
            .update_layout(
                xaxis_title="Date",
                yaxis_title=y_label,
            )
            .for_each_trace(lambda trace: trace.update(name=legend_labels[trace.name])),
            use_container_width=True,
        )

    except ValueError:
        st.write("No data available for this station.")

    st.write("### Seasonal Decomposition")
    try:
        legend_labels = {
            "trend": "Trend",
            "seasonal": "Seasonal",
            "residual": "Residual",
        }

        decomposition = seasonal_decompose(df[decomposition_x], period=12)
        df_dcom = pd.DataFrame(
            {
                "trend": decomposition.trend,
                "seasonal": decomposition.seasonal,
                "residual": decomposition.resid,
                "timestamp": df["timestamp"],
            },
        )
        st.plotly_chart(
            px.line(
                df_dcom,
                x="timestamp",
                y=["trend", "seasonal", "residual"],
            )
            .update_layout(
                xaxis_title="Date",
                yaxis_title="Value",
            )
            .for_each_trace(lambda trace: trace.update(name=legend_labels[trace.name])),
            use_container_width=True,
        )

    except ValueError:
        st.write("Not enough data to decompose the time series.")


def display_page():
    with st.sidebar:
        st.write("**Weather Station Information**")
        station_ids = get_station_list()["station_id"].sort_values()
        station_id = st.selectbox(
            "Select the Station ID", station_ids, index=(len(station_ids) - 1)
        )
        station_info = query_station_info(station_id).to_dict(orient="records")[0]
        st.write(f"""
            **Station ID:** {station_id}

            **Station Name:** {station_info["station_name"]}
        
            **City:** {station_info["city"]}
        
            **Department ID:** {station_info["department_id"]}
        
            **Latitude:** {station_info["latitude"]}
        
            **Longitude:** {station_info["longitude"]}
        
            **Altitude:** {station_info["altitude"]}
            """)

    with st.container(height=400, border=False):
        st.map(pd.DataFrame(station_info, index=[0]), zoom=6, use_container_width=False)
    st.write("# Station Data")

    tab1, tab2 = st.tabs(["Temperature", "Precipitation"])
    with tab1:
        construct_charts("temperature", station_id)
    with tab2:
        construct_charts("precipitation", station_id)


display_page()
