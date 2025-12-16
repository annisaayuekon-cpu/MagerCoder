import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =====================
# CONFIG
# =====================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)

DATA_DIR = "data"

# =====================
# HELPER FUNCTIONS
# =====================
@st.cache_data
def load_csv_safe(path):
    try:
        return pd.read_csv(path)
    except:
        return pd.read_csv(path, sep=";")

def reshape_wb(df):
    df = df.rename(columns={
        df.columns[0]: "country",
        df.columns[1]: "code"
    })
    year_cols = [c for c in df.columns if c.isdigit()]
    df = df.melt(
        id_vars=["country", "code"],
        value_vars=year_cols,
        var_name="year",
        value_name="value"
    )
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()

def classify_type(code):
    return "Country" if len(code) == 3 else "Region"

# =====================
# INDICATOR FILE MAP
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
    "🌐 Perdagangan Internasional": {
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

# =====================
# SIDEBAR (PPI STYLE)
# =====================
st.sidebar.title("📊 Indikator")

category = st.sidebar.radio(
    "Kategori",
    list(INDICATORS.keys())
)

indicator = st.sidebar.selectbox(
    "Indikator",
    list(INDICATORS[category].keys())
)

# =====================
# LOAD DATA
# =====================
file_path = os.path.join(DATA_DIR, INDICATORS[category][indicator])
raw = load_csv_safe(file_path)
df = reshape_wb(raw)
df["type"] = df["code"].apply(classify_type)

# =====================
# FILTER BAR
# =====================
col1, col2, col3 = st.columns(3)

with col1:
    country_filter = st.selectbox(
        "Country (optional)",
        ["All"] + sorted(df[df["type"]=="Country"]["country"].unique())
    )

with col2:
    region_filter = st.selectbox(
        "Region / Aggregate",
        ["All"] + sorted(df[df["type"]=="Region"]["country"].unique())
    )

with col3:
    year_filter = st.slider(
        "Year",
        int(df["year"].min()),
        int(df["year"].max()),
        int(df["year"].max())
    )

# =====================
# APPLY FILTERS
# =====================
filtered = df[df["year"] <= year_filter]

if country_filter != "All":
    filtered = filtered[filtered["country"] == country_filter]

if region_filter != "All":
    filtered = filtered[filtered["country"] == region_filter]

# =====================
# KPI SECTION (PPI STYLE)
# =====================
latest = filtered[filtered["year"] == filtered["year"].max()]

k1, k2, k3, k4 = st.columns(4)

k1.metric("Latest Value", f"{latest['value'].mean():,.2f}")
k2.metric("Countries", df[df["type"]=="Country"]["country"].nunique())
k3.metric("Regions", df[df["type"]=="Region"]["country"].nunique())
k4.metric("Data Points", len(filtered))

# =====================
# TIME SERIES
# =====================
st.subheader("📈 Time Series Trend")

fig_ts = px.line(
    filtered,
    x="year",
    y="value",
    color="country",
    title=f"Trend: {indicator}"
)
st.plotly_chart(fig_ts, use_container_width=True)

# =====================
# TOP 10 / BOTTOM 10
# =====================
st.subheader("🏆 Top 10 & Bottom 10 Countries")

latest_country = latest[latest["type"]=="Country"]

top10 = latest_country.sort_values("value", ascending=False).head(10)
bottom10 = latest_country.sort_values("value").head(10)

c1, c2 = st.columns(2)

with c1:
    st.write("🔼 Top 10")
    st.dataframe(top10[["country","value"]])

with c2:
    st.write("🔽 Bottom 10")
    st.dataframe(bottom10[["country","value"]])

# =====================
# BUBBLE CHART
# =====================
st.subheader("🔵 Country Comparison (Bubble Chart)")

fig_bubble = px.scatter(
    latest_country,
    x="value",
    y="country",
    size="value",
    color="country",
    title="Country Comparison"
)
st.plotly_chart(fig_bubble, use_container_width=True)

# =====================
# MAP
# =====================
st.subheader("🗺 World Map")

fig_map = px.choropleth(
    latest_country,
    locations="code",
    color="value",
    hover_name="country",
    title=indicator
)
st.plotly_chart(fig_map, use_container_width=True)
