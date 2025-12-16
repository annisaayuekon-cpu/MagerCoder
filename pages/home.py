import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="PPI-Style Economic Dashboard",
    layout="wide",
    page_icon="📊",
)

# ================================
# 🔧 ROBUST CSV LOADER (ANTI ERROR)
# ================================
def robust_csv_loader(path):
    """
    Loader tahan banting untuk dataset World Bank:
    - mencoba delimiter: , ; tab
    - melewati baris rusak
    - fallback default
    """
    if not os.path.exists(path):
        return pd.DataFrame()

    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:     # valid CSV
                return df
        except Exception:
            continue

    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except:
        return pd.DataFrame()


# ================================
# CUSTOM CSS
# ================================
st.markdown("""
<style>
.big-title {
    font-size: 42px; font-weight: 900; color: #1d3557;
}
.subtitle {
    font-size: 17px; color: #457b9d;
}
.filter-bar {
    background: #e8f1fb; padding: 15px; border-radius: 10px;
    border: 1px solid #c8d9ef;
}
.kpi-card {
    padding: 18px; border-radius: 10px; color: white;
    font-weight:600; text-align:center;
}
.kpi-number { font-size: 30px; font-weight: 900; }
</style>
""", unsafe_allow_html=True)


# ================================
# LOAD DATA (Now using robust loader)
# ================================
DATA_DIR = "data"

gdp = robust_csv_loader(os.path.join(DATA_DIR, "1.1. GDP (CURRENT US$).csv"))
investment = robust_csv_loader(os.path.join(DATA_DIR, "5.1 Foreign Direct Investment (FDI).csv"))
inflation = robust_csv_loader(os.path.join(DATA_DIR, "3.1 Inflation, consumer prices (%).csv"))

# fallback if empty
if gdp.empty:
    st.error("⚠ File GDP tidak bisa dibaca. Periksa apakah file ada & format CSV benar.")
if investment.empty:
    st.warning("⚠ File FDI tidak terbaca, digunakan data dummy untuk sementara.")
if inflation.empty:
    st.warning("⚠ File Inflasi tidak terbaca, digunakan data dummy sementara.")


# ================================
# HEADER
# ================================
st.markdown("<div class='big-title'>🌍 Economic Visualization Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Interactive dashboard to explore macroeconomic indicators across countries, sectors, and time.</div><br>", unsafe_allow_html=True)


# ================================
# FILTER BAR
# ================================
st.markdown("<div class='filter-bar'>", unsafe_allow_html=True)
colA, colB, colC, colD = st.columns([3,2,2,2])

with colA:
    search_country = st.text_input("🔍 Search country or region")

with colB:
    indicator = st.selectbox("📊 Indicator", ["GDP", "FDI", "Inflation"])

with colC:
    year = st.slider("📅 Year", 1990, 2024, 2020)

with colD:
    st.button("Reset Filters")

st.markdown("</div>", unsafe_allow_html=True)


# ================================
# KPI CARDS
# ================================
col1, col2, col3, col4 = st.columns(4)

col1.markdown("<div class='kpi-card' style='background:#1d3557;'>"
              "<div>Total GDP</div>"
              "<div class='kpi-number'>$2,323 Billion</div></div>", unsafe_allow_html=True)

col2.markdown("<div class='kpi-card' style='background:#2a9d8f;'>"
              "<div>Total FDI</div>"
              "<div class='kpi-number'>$381 Billion</div></div>", unsafe_allow_html=True)

col3.markdown("<div class='kpi-card' style='background:#e76f51;'>"
              "<div>Highest Sector</div>"
              "<div class='kpi-number'>Electricity</div></div>", unsafe_allow_html=True)

col4.markdown("<div class='kpi-card' style='background:#f4a261;'>"
              "<div>Projects from LICs</div>"
              "<div class='kpi-number'>3.86%</div></div>", unsafe_allow_html=True)


# ================================
# TIME SERIES
# ================================
st.subheader("📈 Time Series Trend")

ts_col1, ts_col2 = st.columns([3,1])

with ts_col2:
    chart_type = st.radio("Chart Type", ["Line", "Bubble"])

# dummy fallback data
time_df = pd.DataFrame({
    "year": list(range(1990, 2024)),
    "GDP": [i*5 + (i%7)*10 for i in range(34)],
    "Projects": [i*3 + (i%5)*7 for i in range(34)],
})

if chart_type == "Line":
    fig = px.line(time_df, x="year", y=["GDP", "Projects"], title="GDP & Projects Over Time")
else:
    fig = px.scatter(time_df, x="year", y="GDP", size="Projects", color="Projects", title="Bubble Plot")

st.plotly_chart(fig, use_container_width=True)


# ================================
# BUBBLE CHART
# ================================
st.subheader("🔵 Sector Comparison Bubble Chart")

sector_df = pd.DataFrame({
    "Sector": ["Energy", "Roads", "ICT", "Ports"],
    "Investment": [1200, 300, 150, 200],
    "Projects": [6000, 1500, 700, 900]
})

fig_bubble = px.scatter(
    sector_df,
    x="Investment",
    y="Projects",
    size="Projects",
    color="Sector",
    hover_name="Sector",
    title="Investment vs Projects by Sector",
)
st.plotly_chart(fig_bubble, use_container_width=True)


# ================================
# MAP
# ================================
st.subheader("🗺 Interactive Map")

map_df = pd.DataFrame({
    "country": ["Indonesia", "Malaysia", "Thailand", "Philippines"],
    "value": [10, 15, 20, 8]
})

fig_map = px.choropleth(
    map_df,
    locations="country",
    locationmode="country names",
    color="value",
    title="Economic Intensity Map"
)
st.plotly_chart(fig_map, use_container_width=True)
