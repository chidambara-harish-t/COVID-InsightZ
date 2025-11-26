import streamlit as st
import pandas as pd
from src.load import get_data
from src.transform import summary_stats, global_cases, format_region
from src.viz import plot_daily, plot_global, plot_top10
from src.config import DEFAULT_COUNTRIES
from src.transform import forecast_7day
from src.vizplotly import plot_forecast_px
import src.config as config
if config.USE_PLOTLY:
    from src.vizplotly import plot_daily_px, plot_global_px, plot_top10_px

# Streamlit page settings
st.set_page_config(page_title="COVID Insights", layout="wide")

# Load  data
df = get_data()
df = global_cases(df)
from src import db as dbmod
import src.config as config

#  DB init/load
if config.USE_DB:
    dbmod.init_db(config)
    dbmod.load_to_db(df, config, replace=True)


labels_map = {}
for col in df.columns:
    if col[0] in ["Date", "GlobalCases"]:
        continue
    country, province = col
    if not province or str(province).lower() == "nan":
        display = country
    else:
        display = f"{country} - {province}"
    labels_map[display] = col

# Sidebar header
st.sidebar.header("Available countries:")


default_labels = [c for c in DEFAULT_COUNTRIES if c in labels_map]

# Multiselect list
countries_labels = st.sidebar.multiselect(
    "Select countries to view",
    list(labels_map.keys()),
    default=default_labels
)


countries = [labels_map[l] for l in countries_labels]

# Date range 
min_date, max_date = df[("Date", "")].min(), df[("Date", "")].max()
date_range = st.sidebar.date_input(
    "Select date range:",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filtering by date range
if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df[("Date", "")] >= pd.to_datetime(start_date)) & (df[("Date", "")] <= pd.to_datetime(end_date))]

# Landing Page
st.title("COVID-19 Insights Dashboard")
st.markdown("### This dashboard provides insights into COVID-19 trends by country and globally.")

# latest totals per country/province
latest = df.iloc[-1].drop(labels=[("Date", ""), ("GlobalCases", "")], errors="ignore")
latest = pd.to_numeric(latest, errors="coerce").dropna()

st.subheader("Top 10 Countries by Total Cases (Latest Day)")
fig_top10 = plot_top10(latest)
st.pyplot(fig_top10)

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    [" Daily Trend", " Summary Stats", " Global Trend", " Forecast"]
)
# Top 10 
st.subheader("Top 10 Countries by Total Cases (Latest Day)")
if config.USE_PLOTLY:
    st.plotly_chart(plot_top10_px(latest), use_container_width=True)
else:
    st.pyplot(plot_top10(latest))

with tab1:
    st.subheader("Daily COVID-19 Confirmed Cases by Country")
    if countries:
        if config.USE_PLOTLY:
            st.plotly_chart(plot_daily_px(df, countries), use_container_width=True)
        else:
            st.pyplot(plot_daily(df, countries))

with tab2:
    st.subheader("Summary Stats for Selected Countries")
    if countries:
        stats = summary_stats(df, countries)
        st.table(stats)

        # CSV download for summary stats
        csv = stats.to_csv(index=False).encode("utf-8")
        st.download_button("Download Summary Stats as CSV", csv, "summary_stats.csv", "text/csv")

with tab3:
    st.subheader("Global COVID-19 Confirmed Cases Over Time")
    if config.USE_PLOTLY:
        st.plotly_chart(plot_global_px(df), use_container_width=True)
    else:
        st.pyplot(plot_global(df))

    # CSV download for filtered dataset
    if config.USE_DB:
        long_filtered = dbmod.query_range(config, start_date, end_date, regions=countries)
        csv_all = long_filtered.to_csv(index=False).encode("utf-8")
    else:
        csv_all = df.to_csv(index=False).encode("utf-8")

    st.download_button(" Download Filtered Data as CSV", csv_all, "filtered_data.csv", "text/csv")
# Forecast Tab
with tab4:
    st.subheader("Basic Forecast (7-day Rolling Average Projection)")
    if countries:
        for c in countries: 
            fc = forecast_7day(df, c)
            if config.USE_PLOTLY:
                st.plotly_chart(plot_forecast_px(fc, c), use_container_width=True)
            else:
                st.line_chart(fc.set_index("Date")[["Cases", "7d_avg", "Forecast"]])

        st.caption(" Disclaimer: This forecast is a naive 7-day moving average projection. "
                   "It is not predictive modeling and should not be relied upon for decisions.")

st.markdown("Data source: [JHU CSSE COVID-19 Data](https://www.kaggle.com/datasets/antgoldbloom/covid19-data-from-john-hopkins-university)")