import json
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st
from statsmodels.tsa.seasonal import seasonal_decompose

st.set_page_config(page_title="Climate Change in France", page_icon="🌍", layout="wide")
conn = sqlite3.connect("./data/data.db")

### Data


@st.cache_data
def load_geojson() -> dict:
    """
    Load the geojson file containing the departments shapes.
    """

    with open("./data/raw/departments_shape/departments.geojson") as f:
        data = json.load(f)
    return data


@st.cache_data
def get_station_department_mapping() -> pd.DataFrame:
    """
    Retrieves the mapping between stations and departments from the database.

    Returns:
        pd.DataFrame: A DataFrame containing the station_id and department_id mapping.
    """

    query = """
    SELECT stations.station_id, stations.department_id
    FROM stations
    LEFT JOIN (
    SELECT station_id, department_id
    FROM stations
    WHERE department_id IS NOT NULL
    ) AS departments
    ON stations.station_id = departments.station_id
    """
    df = pd.read_sql(query, conn)
    return df


### Components


def get_department_timerange(department_id: str) -> tuple[int, int]:
    """
    Retrieves the minimum and maximum timestamps for measurements associated with a given department.

    Args:
        department_id (str): The ID of the department.

    Returns:
        tuple[int, int]: A tuple containing the minimum and maximum timestamps as integers.
    """
    
    query = f"""
        SELECT MIN(timestamp), MAX(timestamp)
        FROM measurements
        INNER JOIN (
            SELECT stations.station_id, stations.department_id
            FROM stations
            WHERE department_id = {department_id}
        ) AS departments
        ON departments.station_id = measurements.station_id
        """
    df = pd.read_sql(query, conn)
    min_time, max_time = df.iloc[0]
    min_time = int(min_time[:4])
    max_time = int(max_time[:4])
    return min_time, max_time


def get_time_series(
    department_id: str, variable: str, min_year: int, max_year: int, agg_method="mean"
) -> pd.DataFrame:
    """
    Retrieves time series data for a specific department, variable, and time range.
    
    Args:
        department_id (str): The ID of the department.
        variable (str): The variable to retrieve time series data for.
        min_year (int): The minimum year of the time range.
        max_year (int): The maximum year of the time range.
        agg_method (str, optional): The aggregation method to apply to the time series data. Defaults to "mean".
    
    Returns:
        pd.DataFrame: A DataFrame containing the time series data.
    """

    query = f"""
    SELECT timestamp, measurements.station_id AS station_id, variable, value
    FROM measurements
    INNER JOIN (
        SELECT stations.station_id, stations.department_id
        FROM stations
        WHERE department_id = {department_id}
    ) AS departments
    ON departments.station_id = measurements.station_id
    WHERE variable = '{variable}' AND timestamp BETWEEN "{min_year}-01-01" AND "{max_year}-01-01"
    """
    df = pd.read_sql(query, conn)
    output = df.groupby("timestamp")["value"].agg(agg_method).reset_index()
    return output


def construct_charts(type: str, department: str, time_range: tuple, agg_method: str):
    """
    Construct the charts for the given type of data in a tab.
    """

    match type:
        case "temperature":
            tn = get_time_series(
                department, "TN", time_range[0], time_range[1], agg_method
            )
            tx = get_time_series(
                department, "TX", time_range[0], time_range[1], agg_method
            )
            df = tx.merge(tn, on="timestamp", suffixes=("_max", "_min"))
            min_max_scale = (df["value_min"].min(), df["value_max"].max())
            historical_y = ["value_max", "value_min"]
            decomposition_x = "value_max"
            y_label = "Temperature (°C)"
        case "precipitation":
            df = get_time_series(
                department, "RR", time_range[0], time_range[1], agg_method
            )
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


### Page


def display_page():
    """
    Main function to display the page.
    """
    
    with st.sidebar:
        st.write("## Query Parameters")
        department_code_list = [
            i["properties"]["code"] for i in load_geojson()["features"]
        ]
        department_name_list = [
            i["properties"]["nom"] for i in load_geojson()["features"]
        ]
        display_labels = [
            f"{code} - {name}"
            for code, name in zip(department_code_list, department_name_list)
        ]
        department = st.selectbox(
            "Department",
            department_code_list,
            format_func=lambda x: display_labels[department_code_list.index(str(x))],
        )
        station_count_in_department = (
            get_station_department_mapping()
            .groupby("department_id")
            .size()
            .sort_values(ascending=False)
            .to_frame()
            .loc[int(department)]
            .values[0]
        )
        st.write(
            f"Data of **:green[{station_count_in_department}]** weather stations available in this department"
        )

        min_time, max_time = get_department_timerange(department)
        time_range = st.slider("Time Range", min_time, max_time, (min_time, max_time))

        agg_method = st.radio(
            "Select an aggregation method",
            ["mean", "median"],
            format_func=str.capitalize,
        )

    # TODO: add map
        
    st.write(f"## 🗺️ {department_name_list[department_code_list.index(department)]}")

    tab1, tab2 = st.tabs(["Temperature", "Precipitation"])
    with tab1:
        construct_charts("temperature", department, time_range, agg_method)

    with tab2:
        construct_charts("precipitation", department, time_range, agg_method)


display_page()

