import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =====================================================
# BASIC CONFIG
# =====================================================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    layout="wide"
)

st.title("🌍 Economic Visualization Dashboard")
st.caption("Interactive dashboard using World Bank data (PPI Style)")

# =====================================================
# PATH HANDLING (ANTI ERROR STREAMLIT CLOUD)
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# =====================================================
# LOAD METADATA
# =====================================================
@st.cache_data
def load_metadata():
    path = os.path.join(DATA_DIR, "country_metadata.csv")
    df = pd.read_csv(path)

    df = df.rename(columns={
        "Country Name": "country",
        "Country Code": "code"
    })

    return df

metadata = load_metadata()

# =====================================================
# INDICATOR CONFIG (SESUI PERMINTAAN KAMU)
# =====================================================
INDICATORS = {
    "📈 Pertumbuhan Ekonomi & GDP": {
        "GDP Growth (%)": "1.3 GDP growth (%).csv"
    },
    "👷 Tenaga Kerja & Pengangguran": {
        "Unemployment Rate": "2.2 Unemployment rate.csv"
    },
    "🔥 Inflasi & Harga Konsumen": {
        "Inflation (CPI)": "3.1 Inflation, consumer prices (%).csv"
    },
    "🌍 Perdagangan Internasional": {
        "Exports": "4.1 Exports of goods and services.csv",
        "Imports": "4.2 Imports of goods and services.csv"
    },
    "💼 Investasi (FDI & Kapital)": {
        "FDI": "5.1 Foreign Direct Investment (FDI).csv"
    },
    "📉 Kemiskinan & Ketimpangan": {
        "Gini Index": "6.2 GINI INDEX.csv"
    },
    "👥 Populasi & Demografi": {
        "Total Population": "7.1 TOTAL POPULATION.csv"
    },
    "🎓 Pendidikan": {
        "School Enrollment": "8.1 SCHOOL ENROLLMENT.csv"
    },
    "🏥 Kesehatan": {
        "Health Expenditure": "9.1 HEALTH EXPENDITURE.csv"
    },
    "🌱 Energi & Lingkungan": {
        "CO2 Emissions": "10.1 CO EMISSIONS.csv",
        "Electricity Access": "10.4 ELECTRICITY ACCESS.csv"
    }
}

# =====================================================
# FILTER UI (TOP BAR STYLE)
# =====================================================
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    category = st.selectbox(
        "📂 Kategori Indikator",
        list(INDICATORS.keys())
    )

with col2:
    indicator = st.selectbox(
        "📊 Pilih Indikator",
        list(INDICATORS[category].keys())
    )

with col3:
    country = st.selectbox(
        "🌎 Pilih Negara",
        ["Global"] + sorted(metadata["country"].unique())
    )

# =====================================================
# LOAD INDICATOR DATA
# =====================================================
@st.cache_data
def load_indicator(filename):
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)

    df = df.rename(columns={
        "Country Name": "country",
        "Country Code": "code"
    })

    df = df.melt(
        id_vars=["country", "code"],
        var_name="year",
        value_name="value"
    )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df.dropna(subset=["year"])

filename = INDICATORS[category][indicator]
df = load_indicator(filename)

# =====================================================
# FILTER COUNTRY
# =====================================================
if country != "Global":
    df = df[df["country"] == country]

# =====================================================
# KPI SECTION
# =====================================================
latest_year = df["year"].max()
latest_value = df[df["year"] == latest_year]["value"].mean()

k1, k2, k3 = st.columns(3)

k1.metric("📅 Tahun Terakhir", int(latest_year))
k2.metric("📈 Nilai Rata-rata", f"{latest_value:,.2f}")
k3.metric("🌍 Jumlah Negara", df["country"].nunique())

# =====================================================
# TIME SERIES
# =====================================================
st.subheader("📈 Tren Waktu")

fig_ts = px.line(
    df,
    x="year",
    y="value",
    color="country" if country == "Global" else None,
    labels={"value": indicator, "year": "Tahun"},
    height=420
)

st.plotly_chart(fig_ts, use_container_width=True)

# =====================================================
# TOP 10 & BOTTOM 10
# =====================================================
st.subheader("🏆 Top 10 & Bottom 10 Negara")

latest_df = df[df["year"] == latest_year]

top10 = latest_df.sort_values("value", ascending=False).head(10)
bottom10 = latest_df.sort_values("value").head(10)

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🔼 Top 10")
    st.dataframe(top10[["country", "value"]], use_container_width=True)

with c2:
    st.markdown("### 🔽 Bottom 10")
    st.dataframe(bottom10[["country", "value"]], use_container_width=True)

# =====================================================
# BUBBLE CHART (COUNTRY COMPARISON)
# =====================================================
st.subheader("🫧 Country Comparison (Bubble Chart)")

fig_bubble = px.scatter(
    latest_df,
    x="value",
    y="country",
    size="value",
    hover_name="country",
    size_max=40,
    height=500
)

st.plotly_chart(fig_bubble, use_container_width=True)

# =====================================================
# FOOTNOTE
# =====================================================
st.caption(
    "📌 Data source: World Bank | Visualization inspired by PPI Dashboard"
)
