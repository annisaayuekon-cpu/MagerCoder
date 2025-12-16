# =========================================================
# PPI-STYLE ECONOMIC DASHBOARD (WORLD BANK DATA)
# FINAL VERSION — ANTI PARSER ERROR
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from region_mapping import get_region

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)

# =========================================================
# SAFE CSV LOADER (ANTI ERROR)
# =========================================================
def load_csv_safe(path):
    try:
        return pd.read_csv(path, sep=";", engine="python")
    except:
        try:
            return pd.read_csv(path, sep=",", engine="python")
        except:
            try:
                return pd.read_csv(path, sep="\t", engine="python")
            except:
                return pd.read_csv(path, engine="python", on_bad_lines="skip")

# =========================================================
# DATA CONFIG
# =========================================================
DATA_DIR = "data"

INDICATORS = {
    "GDP Growth (%)": "1.3 GDP growth (%).csv",
    "Unemployment Rate": "2.2 Unemployment rate.csv",
    "Inflation (CPI)": "3.1 Inflation, consumer prices (%).csv",
    "Exports": "4.1 Exports of goods and services.csv",
    "Imports": "4.2 Imports of goods and services.csv",
    "FDI": "5.1 Foreign Direct Investment (FDI).csv",
    "Gini Index": "6.2 GINI INDEX.csv",
    "Total Population": "7.1 TOTAL POPULATION.csv",
    "School Enrollment": "8.1 SCHOOL ENROLLMENT.csv",
    "Health Expenditure": "9.1 HEALTH EXPENDITURE.csv",
    "CO2 Emissions": "10.1 CO EMISSIONS.csv",
    "Electricity Access": "10.4 ELECTRICITY ACCESS.csv",
}

# =========================================================
# LOAD & CLEAN DATA
# =========================================================
@st.cache_data
def load_all_data():
    data = {}
    for label, file in INDICATORS.items():
        path = os.path.join(DATA_DIR, file)
        if os.path.exists(path):
            df = load_csv_safe(path)

            # pastikan kolom utama ada
            if "Country Name" not in df.columns:
                continue

            # reshape wide → long
            year_cols = [c for c in df.columns if c.isdigit()]
            df_long = df.melt(
                id_vars=["Country Name", "Country Code"],
                value_vars=year_cols,
                var_name="Year",
                value_name="Value"
            )

            df_long["Year"] = df_long["Year"].astype(int)
            df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
            df_long["Region"] = df_long["Country Name"].apply(get_region)

            # drop agregat global
            df_long = df_long.dropna(subset=["Region"])

            data[label] = df_long

    return data

DATA = load_all_data()

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("📊 Dashboard Ekonomi")

indicator = st.sidebar.selectbox(
    "Pilih Indikator",
    list(DATA.keys())
)

country = st.sidebar.text_input("Cari Negara (opsional)")

region = st.sidebar.selectbox(
    "Region",
    ["Global"] + sorted(DATA[indicator]["Region"].unique())
)

year = st.sidebar.slider(
    "Tahun",
    int(DATA[indicator]["Year"].min()),
    int(DATA[indicator]["Year"].max()),
    int(DATA[indicator]["Year"].max())
)

# =========================================================
# FILTER DATA
# =========================================================
df = DATA[indicator].copy()

if region != "Global":
    df = df[df["Region"] == region]

if country:
    df = df[df["Country Name"].str.contains(country, case=False)]

df_year = df[df["Year"] == year]

# =========================================================
# HEADER
# =========================================================
st.title("🌍 Economic Visualization Dashboard")
st.caption("Interactive dashboard using World Bank data (PPI-style)")

# =========================================================
# KPI CARDS
# =========================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Latest Value (Region / Global)",
    f"{df_year['Value'].mean():,.2f}"
)

col2.metric(
    "Country Selected",
    country if country else "No Country Selected"
)

col3.metric(
    "Total Countries",
    df_year["Country Name"].nunique()
)

col4.metric(
    "Dataset Rows",
    len(df)
)

st.divider()

# =========================================================
# TIME SERIES
# =========================================================
st.subheader("📈 Time Series Trend")

fig_ts = px.line(
    df if not country else df[df["Country Name"] == country],
    x="Year",
    y="Value",
    color="Country Name" if not country else None,
    title=f"Trend of {indicator}"
)

st.plotly_chart(fig_ts, use_container_width=True)

# =========================================================
# BUBBLE CHART
# =========================================================
st.subheader("🔵 Country Comparison (Bubble Chart)")

fig_bubble = px.scatter(
    df_year,
    x="Value",
    y="Country Name",
    size="Value",
    color="Region",
    title=f"{indicator} by Country ({year})",
    height=600
)

st.plotly_chart(fig_bubble, use_container_width=True)

# =========================================================
# MAP
# =========================================================
st.subheader("🗺 Global Map")

fig_map = px.choropleth(
    df_year,
    locations="Country Name",
    locationmode="country names",
    color="Value",
    hover_name="Country Name",
    title=f"{indicator} ({year})"
)

st.plotly_chart(fig_map, use_container_width=True)

# =========================================================
# DATA TABLE
# =========================================================
with st.expander("📄 Lihat Data Tabel"):
    st.dataframe(df_year.sort_values("Value", ascending=False))
