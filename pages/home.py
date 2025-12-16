import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)

DATA_DIR = "data"

# ======================
# SAFE CSV LOADER
# ======================
@st.cache_data
def load_csv(path):
    for sep in [";", ",", "\t"]:
        try:
            return pd.read_csv(path, sep=sep, engine="python")
        except:
            continue
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

# ======================
# SIDEBAR – CATEGORY & INDICATOR
# ======================
st.sidebar.title("📊 Dashboard Ekonomi")

CATEGORIES = {
    "📈 Pertumbuhan Ekonomi & GDP": {
        "GDP Growth (%)": "1.3 GDP growth (%).csv",
    },
    "👷 Tenaga Kerja & Pengangguran": {
        "Unemployment Rate (%)": "2.2 Unemployment rate.csv",
    },
    "🔥 Inflasi & Harga Konsumen": {
        "Inflation (CPI %)": "3.1 Inflation, consumer prices (%).csv",
    },
    "🌐 Perdagangan Internasional": {
        "Exports of Goods & Services": "4.1 Exports of goods and services.csv",
        "Imports of Goods & Services": "4.2 Imports of goods and services.csv",
    },
    "💼 Investasi (FDI & Kapital)": {
        "Foreign Direct Investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
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
        "Electricity Access (%)": "10.4 ELECTRICITY ACCESS.csv",
    },
}

category = st.sidebar.radio("Pilih Kategori", list(CATEGORIES.keys()))
indicator = st.sidebar.selectbox(
    "Pilih Indikator",
    list(CATEGORIES[category].keys())
)

file_name = CATEGORIES[category][indicator]

# ======================
# HEADER
# ======================
st.markdown("## 🌍 Economic Visualization Dashboard")
st.caption("Interactive dashboard using World Bank data (PPI-style layout)")

# ======================
# FILTER BAR
# ======================
c1, c2, c3 = st.columns([3, 2, 2])

with c1:
    country_search = st.text_input("🔍 Search Country (optional)")

with c2:
    year = st.slider("📅 Year", 1990, 2024, 2020)

with c3:
    st.write("")
    st.write("")

# ======================
# LOAD & TRANSFORM DATA
# ======================
df = load_csv(os.path.join(DATA_DIR, file_name))

year_cols = [c for c in df.columns if c.isdigit()]

df_long = df.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=year_cols,
    var_name="year",
    value_name="value"
)

df_long["year"] = df_long["year"].astype(int)
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")

df_year = df_long[df_long["year"] == year]

if country_search:
    df_year = df_year[
        df_year["Country Name"]
        .str.contains(country_search, case=False, na=False)
    ]

# ======================
# KPI CARDS
# ======================
k1, k2, k3, k4 = st.columns(4)

latest_val = df_year["value"].mean()

k1.metric("Selected Indicator", indicator)
k2.metric("Year", year)
k3.metric("Countries", df_year["Country Name"].nunique())
k4.metric("Avg Value", f"{latest_val:,.2f}" if pd.notna(latest_val) else "—")

st.divider()

# ======================
# TIME SERIES
# ======================
st.subheader("📈 Time Series Trend")

fig_ts = px.line(
    df_long,
    x="year",
    y="value",
    color="Country Name",
    title=f"{indicator} Over Time"
)
fig_ts.update_layout(showlegend=False)
st.plotly_chart(fig_ts, use_container_width=True)

# ======================
# BUBBLE CHART
# ======================
st.subheader("🔵 Country Comparison (Bubble Chart)")

fig_bubble = px.scatter(
    df_year,
    x="value",
    y="Country Name",
    size="value",
    color="Country Name",
    title=f"{indicator} Comparison – {year}",
    height=600
)
fig_bubble.update_layout(showlegend=False)
st.plotly_chart(fig_bubble, use_container_width=True)

# ======================
# MAP
# ======================
st.subheader("🗺 World Map")

fig_map = px.choropleth(
    df_year,
    locations="Country Code",
    color="value",
    hover_name="Country Name",
    color_continuous_scale="Blues",
    title=f"{indicator} in {year}"
)
st.plotly_chart(fig_map, use_container_width=True)

# ======================
# TOP / BOTTOM 10
# ======================
st.subheader("🏆 Top & Bottom 10 Countries")

df_rank = df_year.dropna(subset=["value"])

top10 = df_rank.sort_values("value", ascending=False).head(10)
bottom10 = df_rank.sort_values("value").head(10)

t1, t2 = st.columns(2)

with t1:
    st.markdown("### 🔝 Top 10")
    st.table(top10[["Country Name", "value"]].reset_index(drop=True))

with t2:
    st.markdown("### 🔻 Bottom 10")
    st.table(bottom10[["Country Name", "value"]].reset_index(drop=True))
