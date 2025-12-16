import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)

# =====================
# STYLE (PPI-LIKE)
# =====================
st.markdown("""
<style>
body { background-color: #f5f7fb; }
h1, h2, h3 { color: #1f2c56; }
.kpi {
    background: white;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.kpi h2 { margin: 0; font-size: 26px; }
.kpi p { margin: 0; color: #666; }
hr { border: 2px solid #1f77b4; }
</style>
""", unsafe_allow_html=True)

# =====================
# INDICATOR CONFIG
# =====================
INDICATORS = {
    "📈 Pertumbuhan Ekonomi & GDP": {
        "GDP Growth (%)": "1.3 GDP growth (%).csv"
    },
    "👷 Tenaga Kerja & Pengangguran": {
        "Unemployment Rate (%)": "2.2 Unemployment rate.csv"
    },
    "🔥 Inflasi & Harga Konsumen": {
        "Inflation (%)": "3.1 Inflation, consumer prices (%).csv"
    },
    "🌍 Perdagangan Internasional": {
        "Exports (US$)": "4.1 Exports of goods and services.csv",
        "Imports (US$)": "4.2 Imports of goods and services.csv"
    },
    "💼 Investasi": {
        "FDI (US$)": "5.1 Foreign Direct Investment (FDI).csv"
    },
    "📉 Ketimpangan": {
        "Gini Index": "6.2 GINI INDEX.csv"
    },
    "👥 Populasi": {
        "Total Population": "7.1 TOTAL POPULATION.csv"
    },
    "🎓 Pendidikan": {
        "School Enrollment": "8.1 SCHOOL ENROLLMENT.csv"
    },
    "🏥 Kesehatan": {
        "Health Expenditure": "9.1 HEALTH EXPENDITURE.csv"
    },
    "🌱 Energi & Lingkungan": {
        "CO₂ Emissions": "10.1 CO EMISSIONS.csv",
        "Electricity Access (%)": "10.4 ELECTRICITY ACCESS.csv"
    }
}

DATA_DIR = "data"

# =====================
# LOAD & CLEAN DATA
# =====================
@st.cache_data
def load_indicator(file):
    df = pd.read_csv(os.path.join(DATA_DIR, file))
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

# =====================
# HEADER
# =====================
st.title("🌍 Economic Visualization Dashboard")
st.caption("Interactive dashboard using World Bank data (PPI Style)")

# =====================
# FILTER BAR
# =====================
col1, col2, col3, col4 = st.columns([3, 3, 2, 2])

with col1:
    country_search = st.text_input("🔍 Search Country (optional)")

with col2:
    category = st.selectbox("📂 Indicator Category", list(INDICATORS.keys()))
    indicator_label = st.selectbox(
        "📊 Indicator",
        list(INDICATORS[category].keys())
    )

with col3:
    year = st.slider("📅 Year", 1990, 2024, 2022)

with col4:
    view_mode = st.radio("View Mode", ["Global", "Single Country"])

# =====================
# DATA FILTERING
# =====================
df = load_indicator(INDICATORS[category][indicator_label])

if country_search:
    df = df[df["country"].str.contains(country_search, case=False)]

if view_mode == "Single Country":
    country = st.selectbox("Select Country", sorted(df["country"].unique()))
    df = df[df["country"] == country]

df_year = df[df["year"] == year]

# =====================
# KPI SECTION
# =====================
st.markdown("<hr>", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"<div class='kpi'><p>Latest Value</p><h2>{df_year['value'].mean():,.2f}</h2></div>", unsafe_allow_html=True)

with k2:
    st.markdown(f"<div class='kpi'><p>Total Countries</p><h2>{df_year['country'].nunique()}</h2></div>", unsafe_allow_html=True)

with k3:
    st.markdown(f"<div class='kpi'><p>Indicator</p><h2>{indicator_label}</h2></div>", unsafe_allow_html=True)

with k4:
    st.markdown(f"<div class='kpi'><p>Year</p><h2>{year}</h2></div>", unsafe_allow_html=True)

# =====================
# TIME SERIES
# =====================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("📈 Time Series Trend")

fig_ts = px.line(
    df,
    x="year",
    y="value",
    color="country" if view_mode == "Global" else None
)
st.plotly_chart(fig_ts, use_container_width=True)

# =====================
# TOP & BOTTOM 10
# =====================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🏆 Top & Bottom 10 Countries")

top = df_year.sort_values("value", ascending=False).head(10)
bottom = df_year.sort_values("value").head(10)

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🔝 Top 10")
    st.dataframe(top[["country", "value"]])

with c2:
    st.markdown("### 🔻 Bottom 10")
    st.dataframe(bottom[["country", "value"]])

# =====================
# BUBBLE CHART
# =====================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🫧 Country Comparison")

fig_bubble = px.scatter(
    df_year,
    x="value",
    y="country",
    size="value",
    color="country",
    height=600
)
st.plotly_chart(fig_bubble, use_container_width=True)

# =====================
# WORLD MAP
# =====================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🗺 Global Distribution Map")

fig_map = px.choropleth(
    df_year,
    locations="code",
    color="value",
    hover_name="country",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_map, use_container_width=True)

# =====================
# EXPORT
# =====================
st.download_button(
    "📥 Download Filtered Data (CSV)",
    data=df.to_csv(index=False),
    file_name=f"{indicator_label}.csv",
    mime="text/csv"
)
