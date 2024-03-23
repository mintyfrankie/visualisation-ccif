import streamlit as st

st.set_page_config(page_title="Climate Change in France", page_icon="🌍", layout="wide")

"""
# Climate Change in France
## Visualization - Database Changement climatique

This dashboard provides an interactive exploration of weather trends in France, leveraging data from data.gouv.fr: [https://www.data.gouv.fr/en/](https://www.data.gouv.fr/en/).

**Datasets:**

* **Longues Séries Homogénéisées (LSH):** This dataset offers long-term, consistent weather data for key variables:
    
    * Minimum Temperature (TN)
    * Maximum Temperature (TX)
    * Precipitation (RR)
    * Sunshine Duration (IN)
* **Informations sur les Stations Météo (Station Metadata):** This dataset provides details on meteorological stations, enabling geospatial analysis.

**Functionality:**

This dashboard allows you to visualize:

* **Temporal Trends:** Explore how key weather metrics (temperature, precipitation, sunshine) have changed across France over time.
* **Spatial Variations:** Analyze weather patterns and trends across different regions using the interactive map.

**Value:**

Insights gained from this data are crucial for understanding climate change's impact on French weather. Stakeholders such as policymakers, environmental agencies, and the agricultural sector can utilize this information to develop data-driven adaptation and mitigation strategies.

**Further Exploration:**

Navigate the dashboard to explore the data in detail. Use the interactive features to gain deeper insights into climate change trends across France.
"""
