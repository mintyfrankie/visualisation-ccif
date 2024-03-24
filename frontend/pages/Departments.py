import json
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Climate Change in France", page_icon="🌍", layout="wide")
conn = sqlite3.connect("./data/data.db")


@st.cache_data
def load_geojson():
    with open("./data/raw/departments_shape/departments.geojson") as f:
        data = json.load(f)
    return data


def draw_department_shape(code: str, data: dict) -> px.choropleth_mapbox:
    fig = px.choropleth_mapbox(
        geojson=data,
        locations=[code],
        featureidkey="properties.code",
        color=[1],
        center={"lat": 46.603354, "lon": 1.888334},
        zoom=4,
        opacity=0.5,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_coloraxes(showscale=False)
    return fig


def display_page():
    with st.sidebar:
        st.write("## Department Information")
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
            "Select a department",
            department_code_list,
            format_func=lambda x: display_labels[department_code_list.index(str(x))],
        )

    # FIXME: the following line is not working
    with st.container(height=500, border=False):
        st.plotly_chart(
            draw_department_shape(department, load_geojson()), use_container_width=True
        )
    st.write(f"## 🗺️ {department_name_list[department_code_list.index(department)]}")

    tab1, tab2 = st.tabs(["Temperature", "Precipitation"])
    with tab1:
        pass
    with tab2:
        pass


display_page()
