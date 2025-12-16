import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Dashboard Ekonomi – Ringkasan",
    layout="wide"
)

# =====================================================
# PATH
# =====================================================
DATA_DIR = "data"

# =====================================================
# LOADERS
# =====================================================
@st.cache_data
def load_indicator(filename: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, filename))

@st.cache_data
def load_country_metadata() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, "country_metadata.csv"))

# =====================================================
# LOAD METADATA
# =====================================================
country_meta = load_country_metadata()

# =====================================================
# HEADER
# =====================================================
st.title("📊 Dashboard Ekonomi")
st.caption("Gaya World Bank / PPI")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("Filter")

indicator_files = sorted(
    f for f in os.listdir(DATA_DIR)
    if f.endswith(".csv") and f != "country_metadata.csv"
)

indicator = st.sidebar.selectbox(
    "Indikator",
    indicator_files
)

df = load_indicator(indicator)

# =====================================================
# VALIDATION
# =====================================================
required_cols = {"Country", "Country Code", "Year", "Value"}
if not required_cols.issubset(df.columns):
    st.error("Struktur CSV indikator tidak sesuai")
    st.stop()

# =====================================================
# MERGE METADATA (INI KUNCI)
# =====================================================
df = df.merge(
    country_meta,
    on=["Country", "Country Code"],
    how="left"
)

# =====================================================
# FILTERS
# =====================================================
countries = sorted(df["Country"].dropna().unique())

selected_countries = st.sidebar.multiselect(
    "Negara",
    countries,
    default=countries[:5]
)

year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Tahun",
    year_min,
    year_max,
    (year_min, year_max)
)

regions = sorted(df["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "Region",
    regions,
    default=regions
)

# =====================================================
# APPLY FILTER
# =====================================================
df_filtered = df[
    (df["Country"].isin(selected_countries)) &
    (df["Year"].between(*year_range)) &
    (df["Region"].isin(selected_regions))
]

# =====================================================
# METRICS
# =====================================================
latest_year = df_filtered["Year"].max()
df_latest = df_filtered[df_filtered["Year"] == latest_year]

col1, col2, col3 = st.columns(3)
col1.metric("Tahun", latest_year)
col2.metric("Negara", df_latest["Country"].nunique())
col3.metric("Rata-rata", round(df_latest["Value"].mean(), 2))

# =====================================================
# LINE CHART
# =====================================================
st.subheader(indicator.replace(".csv", ""))

fig_line = px.line(
    df_filtered,
    x="Year",
    y="Value",
    color="Country",
    markers=True
)

st.plotly_chart(fig_line, use_container_width=True)

# =====================================================
# MAP
# =====================================================
st.subheader("Peta Global")

fig_map = px.choropleth(
    df_latest,
    locations="Country Code",
    color="Value",
    hover_name="Country",
    color_continuous_scale="Blues"
)

st.plotly_chart(fig_map, use_container_width=True)

# =====================================================
# REGION SUMMARY
# =====================================================
st.subheader("Rata-rata per Region")

region_summary = (
    df_latest
    .groupby("Region", as_index=False)["Value"]
    .mean()
)

fig_bar = px.bar(
    region_summary,
    x="Region",
    y="Value",
    color="Region"
)

st.plotly_chart(fig_bar, use_container_width=True)

# =====================================================
# DATA TABLE
# =====================================================
with st.expander("Lihat Data"):
    st.dataframe(df_filtered, use_container_width=True)
