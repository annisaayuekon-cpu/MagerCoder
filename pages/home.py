

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    layout="wide",
    page_icon="🌍"
)

# =========================
# CSS – PPI STYLE
# =========================
st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
.title {font-size:34px;font-weight:800;color:#1f3c88;}
.subtitle {font-size:15px;color:#5a6e8c;margin-bottom:20px;}
.filter {background:#e9f2ff;padding:16px;border-radius:12px;border:1px solid #cfe0ff;}
.kpi {background:white;border-radius:14px;padding:18px;
      box-shadow:0 4px 14px rgba(0,0,0,0.06);text-align:center;}
.kpi h3 {font-size:14px;color:#6b7280;}
.kpi h1 {font-size:26px;font-weight:800;}
.section {font-size:22px;font-weight:700;color:#1f3c88;margin-top:28px;}
.note {font-size:12px;color:#6b7280;margin-top:12px;}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<div class="title">🌍 Economic Visualization Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Interactive dashboard using World Bank data (PPI Style)</div>', unsafe_allow_html=True)

# =========================
# LOAD METADATA
# =========================
@st.cache_data
def load_metadata():
    meta = pd.read_csv("data/country_metadata.csv")
    meta = meta.rename(columns={
        "Country Name": "country",
        "Country Code": "code"
    })
    return meta

metadata = load_metadata()

# =========================
# INDICATOR CONFIG
# =========================
DATA_DIR = "data"

INDICATORS = {
    "📈 Pertumbuhan Ekonomi & GDP": {
        "GDP Growth (%)": "1.3 GDP growth (%).csv",
    },
    "👷 Tenaga Kerja & Pengangguran": {
        "Unemployment Rate (%)": "2.2 Unemployment rate.csv",
    },
    "🔥 Inflasi & Harga Konsumen": {
        "Inflation (%)": "3.1 Inflation, consumer prices (%).csv",
    },
    "🌐 Perdagangan Internasional": {
        "Exports": "4.1 Exports of goods and services.csv",
        "Imports": "4.2 Imports of goods and services.csv",
    },
    "💼 Investasi (FDI)": {
        "FDI": "5.1 Foreign Direct Investment (FDI).csv",
    },
    "📉 Ketimpangan": {
        "Gini Index": "6.2 GINI INDEX.csv",
    },
    "👥 Populasi": {
        "Total Population": "7.1 TOTAL POPULATION.csv",
    },
    "🎓 Pendidikan": {
        "School Enrollment": "8.1 SCHOOL ENROLLMENT.csv",
    },
    "🏥 Kesehatan": {
        "Health Expenditure": "9.1 HEALTH EXPENDITURE.csv",
    },
    "🌱 Energi & Lingkungan": {
        "CO₂ Emissions": "10.1 CO EMISSIONS.csv",
        "Electricity Access": "10.4 ELECTRICITY ACCESS.csv",
    }
}

# =========================
# LOAD INDICATOR DATA
# =========================
@st.cache_data
def load_indicator(path):
    df = pd.read_csv(path, sep=None, engine="python")

    df = df.rename(columns={
        df.columns[0]: "country",
        df.columns[1]: "code"
    })

    df = df.melt(
        id_vars=["country", "code"],
        var_name="year",
        value_name="value"
    )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna(subset=["year", "value"])

    # merge metadata
    df = df.merge(metadata, on=["country", "code"], how="left")

    # identify aggregate
    df["type"] = df["code"].apply(lambda x: "Country" if len(str(x)) == 3 else "Aggregate")

    return df

# =========================
# FILTER BAR
# =========================
with st.container():
    st.markdown('<div class="filter">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([3,3,2,2])

    with c1:
        category = st.selectbox("📂 Kategori", list(INDICATORS.keys()))

    with c2:
        indicator = st.selectbox("📊 Indikator", list(INDICATORS[category].keys()))

    with c3:
        region = st.selectbox(
            "🌍 Region",
            ["All"] + sorted(metadata["Region"].dropna().unique().tolist())
        )

    with c4:
        year = st.slider("📅 Tahun", 1990, 2024, 2022)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
file_path = os.path.join(DATA_DIR, INDICATORS[category][indicator])
df = load_indicator(file_path)

if region != "All":
    df = df[df["Region"] == region]

# =========================
# KPI
# =========================
latest = df[df["year"] == year]

k1, k2, k3, k4 = st.columns(4)

k1.markdown(f"<div class='kpi'><h3>Rata-rata Nilai</h3><h1>{latest['value'].mean():,.2f}</h1></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi'><h3>Jumlah Negara</h3><h1>{latest[latest.type=='Country']['country'].nunique()}</h1></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi'><h3>Region</h3><h1>{region}</h1></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='kpi'><h3>Observasi</h3><h1>{len(latest)}</h1></div>", unsafe_allow_html=True)

# =========================
# TIME SERIES
# =========================
st.markdown('<div class="section">📈 Time Series</div>', unsafe_allow_html=True)

fig_ts = px.line(
    df[df["type"]=="Country"],
    x="year",
    y="value",
    color="country",
)
st.plotly_chart(fig_ts, use_container_width=True)

# =========================
# TOP & BOTTOM 10
# =========================
st.markdown('<div class="section">🏆 Top 10 & Bottom 10</div>', unsafe_allow_html=True)

rank = latest[latest["type"]=="Country"].sort_values("value")

c1, c2 = st.columns(2)
c1.dataframe(rank.tail(10)[["country","value"]], use_container_width=True)
c2.dataframe(rank.head(10)[["country","value"]], use_container_width=True)

# =========================
# BUBBLE CHART
# =========================
st.markdown('<div class="section">🔵 Country Comparison</div>', unsafe_allow_html=True)

fig_bubble = px.scatter(
    rank,
    x="value",
    y="country",
    size="value",
    color="Region",
    hover_name="country"
)
st.plotly_chart(fig_bubble, use_container_width=True)

# =========================
# WORLD MAP
# =========================
st.markdown('<div class="section">🗺 World Map</div>', unsafe_allow_html=True)

fig_map = px.choropleth(
    rank,
    locations="code",
    color="value",
    hover_name="country",
)
st.plotly_chart(fig_map, use_container_width=True)

# =========================
# FOOTNOTE
# =========================
st.markdown("""
<div class="note">
Data Source: World Bank Open Data • Includes country & aggregate series
</div>
""", unsafe_allow_html=True)
