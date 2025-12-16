import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)

DATA_DIR = "data"

# =====================
# SAFE CSV LOADER
# =====================
def load_csv_safe(path):
    for sep in [";", ",", "\t"]:
        try:
            return pd.read_csv(path, sep=sep, engine="python")
        except:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

# =====================
# INDICATOR CONFIG (SESUSAI PILIHAN KAMU)
# =====================
INDICATORS = {
    "GDP Growth (%)": "1.3 GDP growth (%).csv",
    "Unemployment Rate (%)": "2.2 Unemployment rate.csv",
    "Inflation (CPI %)": "3.1 Inflation, consumer prices (%).csv",
    "Exports of Goods & Services": "4.1 Exports of goods and services.csv",
    "Imports of Goods & Services": "4.2 Imports of goods and services.csv",
    "Foreign Direct Investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
    "Gini Index": "6.2 GINI INDEX.csv",
    "Total Population": "7.1 TOTAL POPULATION.csv",
    "School Enrollment": "8.1 SCHOOL ENROLLMENT.csv",
    "Health Expenditure": "9.1 HEALTH EXPENDITURE.csv",
    "CO₂ Emissions": "10.1 CO EMISSIONS.csv",
    "Electricity Access (%)": "10.4 ELECTRICITY ACCESS.csv",
}

# =====================
# HEADER
# =====================
st.title("🌍 Economic Visualization Dashboard")
st.caption("Interactive dashboard using World Bank data")

# =====================
# FILTERS
# =====================
f1, f2, f3 = st.columns([3, 3, 2])

with f1:
    country_filter = st.text_input("🔍 Search Country")

with f2:
    indicator = st.selectbox("📊 Select Indicator", list(INDICATORS.keys()))

with f3:
    year = st.slider("📅 Year", 1990, 2024, 2020)

# =====================
# LOAD DATA
# =====================
df = load_csv_safe(os.path.join(DATA_DIR, INDICATORS[indicator]))

# =====================
# RESHAPE WIDE → LONG
# =====================
year_cols = [c for c in df.columns if c.isdigit()]

df_long = df.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=year_cols,
    var_name="year",
    value_name="value"
)

df_long["year"] = df_long["year"].astype(int)

# =====================
# APPLY FILTER
# =====================
df_plot = df_long[df_long["year"] == year]

if country_filter:
    df_plot = df_plot[
        df_plot["Country Name"]
        .str.contains(country_filter, case=False, na=False)
    ]

# =====================
# KPI
# =====================
k1, k2, k3 = st.columns(3)

k1.metric("Countries", df_plot["Country Name"].nunique())
k2.metric("Year", year)
k3.metric("Data Rows", len(df_plot))

# =====================
# TIME SERIES
# =====================
st.subheader("📈 Time Series Trend")

fig_ts = px.line(
    df_long,
    x="year",
    y="value",
    color="Country Name",
    title=f"{indicator} Over Time"
)

st.plotly_chart(fig_ts, use_container_width=True)

# =====================
# MAP
# =====================
st.subheader("🗺 World Map")

fig_map = px.choropleth(
    df_plot,
    locations="Country Code",
    color="value",
    hover_name="Country Name",
    color_continuous_scale="Blues",
    title=f"{indicator} in {year}"
)

st.plotly_chart(fig_map, use_container_width=True)
