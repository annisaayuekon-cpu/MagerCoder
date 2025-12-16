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
# PPI STYLE CSS
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", sans-serif;
}

.block-container {
    padding-top: 1.2rem;
}

.ppi-title {
    font-size: 34px;
    font-weight: 800;
    color: #1f3c88;
}

.ppi-subtitle {
    font-size: 15px;
    color: #5a6e8c;
    margin-bottom: 20px;
}

.filter-box {
    background: #e9f2ff;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #cfe0ff;
    margin-bottom: 25px;
}

.kpi {
    background: white;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    text-align: center;
}

.kpi h3 {
    font-size: 14px;
    color: #6b7280;
}

.kpi h1 {
    font-size: 28px;
    font-weight: 800;
}

.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #1f3c88;
    margin-top: 25px;
    margin-bottom: 10px;
}

.footnote {
    font-size: 12px;
    color: #6b7280;
    margin-top: 15px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<div class="ppi-title">🌍 Economic Visualization Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="ppi-subtitle">Interactive dashboard using World Bank data (PPI-style)</div>', unsafe_allow_html=True)

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
    "💼 Investasi (FDI & Kapital)": {
        "FDI": "5.1 Foreign Direct Investment (FDI).csv",
    },
    "📉 Kemiskinan & Ketimpangan": {
        "Gini Index": "6.2 GINI INDEX.csv",
    },
    "👥 Populasi & Demografi": {
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
# LOAD & CLEAN DATA
# =========================
@st.cache_data
def load_indicator(path):
    df = pd.read_csv(
        path,
        sep=None,
        engine="python"
    )

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

    df["type"] = df["code"].apply(lambda x: "Region" if len(str(x)) != 3 else "Country")
    return df.dropna(subset=["year", "value"])

# =========================
# FILTER BAR
# =========================
with st.container():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([3,3,2,2])

    with c1:
        category = st.selectbox("📂 Indicator Category", list(INDICATORS.keys()))

    with c2:
        indicator = st.selectbox("📊 Indicator", list(INDICATORS[category].keys()))

    with c3:
        year_selected = st.slider("📅 Year", 1990, 2024, 2022)

    with c4:
        country_filter = st.selectbox("🌍 Country", ["All"])

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# LOAD SELECTED DATA
# =========================
file_path = os.path.join(DATA_DIR, INDICATORS[category][indicator])
df = load_indicator(file_path)

countries = sorted(df[df["type"]=="Country"]["country"].unique())
country_filter = st.selectbox("🌍 Country", ["All"] + countries)

filtered = df[df["year"] == year_selected]
if country_filter != "All":
    filtered = filtered[filtered["country"] == country_filter]

# =========================
# KPI
# =========================
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"<div class='kpi'><h3>Latest Value</h3><h1>{filtered['value'].mean():,.2f}</h1></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi'><h3>Total Countries</h3><h1>{df[df.type=='Country']['country'].nunique()}</h1></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi'><h3>Regions / Aggregates</h3><h1>{df[df.type=='Region']['country'].nunique()}</h1></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi'><h3>Observations</h3><h1>{len(filtered)}</h1></div>", unsafe_allow_html=True)

# =========================
# TIME SERIES
# =========================
st.markdown('<div class="section-title">📈 Time Series Trend</div>', unsafe_allow_html=True)

ts = df if country_filter == "All" else df[df["country"] == country_filter]

fig_ts = px.line(
    ts,
    x="year",
    y="value",
    color="country" if country_filter=="All" else None,
)
st.plotly_chart(fig_ts, use_container_width=True)

# =========================
# TOP & BOTTOM 10
# =========================
st.markdown('<div class="section-title">🏆 Top 10 & Bottom 10 Countries</div>', unsafe_allow_html=True)

rank = filtered[filtered["type"]=="Country"].sort_values("value")

c1, c2 = st.columns(2)
c1.dataframe(rank.tail(10)[["country","value"]])
c2.dataframe(rank.head(10)[["country","value"]])

# =========================
# BUBBLE CHART
# =========================
st.markdown('<div class="section-title">🔵 Country Comparison (Bubble Chart)</div>', unsafe_allow_html=True)

fig_bubble = px.scatter(
    rank,
    x="value",
    y="country",
    size="value",
    hover_name="country"
)
st.plotly_chart(fig_bubble, use_container_width=True)

# =========================
# WORLD MAP
# =========================
st.markdown('<div class="section-title">🗺 World Map</div>', unsafe_allow_html=True)

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
<div class="footnote">
⚠️ Data source: World Bank Open Data. Values include country and aggregate series.
</div>
""", unsafe_allow_html=True)
