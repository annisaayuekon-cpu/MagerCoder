import streamlit as st
import pandas as pd
import plotly.express as px
import os


# ======================================================
# STREAMLIT PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)


# ======================================================
# SIMPLE REGION MAPPING (tanpa file lain)
# ======================================================
def get_region(country):
    country = str(country)

    if country in [
        "Indonesia", "Malaysia", "Thailand", "Vietnam", "China", "Japan", "Korea, Rep.",
        "Philippines", "Singapore", "Myanmar", "Lao PDR", "Cambodia", "Mongolia"
    ]:
        return "East Asia & Pacific"

    if country in [
        "United States", "Canada"
    ]:
        return "North America"

    if country in [
        "Germany", "France", "United Kingdom", "Italy", "Spain", "Netherlands",
        "Belgium", "Norway", "Sweden", "Finland", "Turkey", "Poland", "Portugal",
        "Greece", "Austria", "Ireland"
    ]:
        return "Europe & Central Asia"

    if country in [
        "Brazil", "Argentina", "Chile", "Colombia", "Peru", "Mexico"
    ]:
        return "Latin America & Caribbean"

    if country in [
        "India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"
    ]:
        return "South Asia"

    if country in [
        "Saudi Arabia", "United Arab Emirates", "Qatar", "Bahrain", "Iran", "Iraq",
        "Kuwait", "Jordan", "Morocco", "Tunisia", "Algeria", "Egypt"
    ]:
        return "Middle East & North Africa"

    if country in [
        "Nigeria", "Kenya", "Ghana", "Ethiopia", "Tanzania", "Uganda",
        "South Africa", "Senegal", "Rwanda", "Zimbabwe"
    ]:
        return "Sub-Saharan Africa"

    return "Other"


# ======================================================
# LOAD INDICATORS
# ======================================================
DATA_DIR = "data"

INDICATOR_FILES = {
    # GDP & Economy
    "GDP (Current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per Capita": "1.2. GDP PER CAPITA.csv",
    "GDP Growth (%)": "1.3 GDP growth (%).csv",

    # Labor
    "Unemployment Rate": "2.2 Unemployment rate.csv",
    "Youth Unemployment": "2.3 Youth unemployment.csv",

    # Inflation
    "Inflation (Consumer Prices)": "3.1 Inflation, consumer prices (%).csv",

    # Trade
    "Exports of Goods & Services": "4.1 Exports of goods and services.csv",
    "Imports of Goods & Services": "4.2 Imports of goods and services.csv",
    "Trade Openness": "4.4 Trade openness.csv",

    # Investment
    "Foreign Direct Investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",

    # Inequality
    "GINI Index": "6.2. GINI INDEX.csv",

    # Population
    "Total Population": "7.1. TOTAL POPULATION.csv",

    # Education
    "School Enrollment": "8.1. SCHOOL ENROLLMENT.csv",

    # Health
    "Health Expenditure": "9.1. HEALTH EXPENDITURE.csv",

    # Environment
    "CO2 Emissions": "10.1. CO EMISSIONS.csv",
    "Electricity Access": "10.4. ELECTRICITY ACCESS.csv",
}

datasets = {}

for label, file in INDICATOR_FILES.items():
    path = os.path.join(DATA_DIR, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["Region"] = df["Country Name"].apply(get_region)
        datasets[label] = df


# ======================================================
# HEADER
# ======================================================
st.markdown("""
<h1 style='color:#1d3557; font-weight:900;'>🌍 Economic Visualization Dashboard</h1>
<p style='color:#457b9d; font-size:18px;'>
Interactive dashboard using World Bank indicators.
</p>
""", unsafe_allow_html=True)


# ======================================================
# FILTER BAR
# ======================================================
st.markdown("### 🔍 Filters")

colA, colB, colC, colD = st.columns([3, 3, 2, 2])

with colA:
    search_country = st.text_input("Search Country (optional)")

with colB:
    selected_indicator = st.selectbox("Select Indicator", list(INDICATOR_FILES.keys()))

with colC:
    selected_region = st.selectbox(
        "Region",
        ["Global",
         "East Asia & Pacific",
         "Europe & Central Asia",
         "Latin America & Caribbean",
         "Middle East & North Africa",
         "South Asia",
         "Sub-Saharan Africa",
         "North America"]
    )

with colD:
    year = st.slider("Year", 1990, 2024, 2020)


# ======================================================
# PROCESS DATA
# ======================================================
df = datasets[selected_indicator].copy()

# Region filter
if selected_region != "Global":
    df = df[df["Region"] == selected_region]

# Country search filter
if search_country:
    df = df[df["Country Name"].str.contains(search_country, case=False)]

# Reshape to long format
melt_df = df.melt(id_vars=["Country Name", "Country Code", "Region"],
                  var_name="year", value_name="value")

melt_df["year"] = pd.to_numeric(melt_df["year"], errors="coerce")
melt_df = melt_df.dropna()


# ======================================================
# KPI SECTION
# ======================================================
st.markdown("### 📊 Key Metrics")

col1, col2, col3 = st.columns(3)

latest_value = melt_df[melt_df["year"] == year]["value"].sum()

col1.metric("Latest Value", f"{latest_value:,.2f}")
col2.metric("Total Countries", df["Country Name"].nunique())
col3.metric("Dataset Rows", len(melt_df))


# ======================================================
# TIME SERIES CHART
# ======================================================
st.markdown("### 📈 Time Series Trend")

fig = px.line(
    melt_df,
    x="year",
    y="value",
    color="Country Name",
    title=f"Trend of {selected_indicator}",
    height=500
)

st.plotly_chart(fig, use_container_width=True)


# ======================================================
# BUBBLE CHART COMPARISON
# ======================================================
st.markdown("### 🔵 Country Comparison (Bubble Chart)")

latest_df = melt_df[melt_df["year"] == year]

fig_bubble = px.scatter(
    latest_df,
    x="value",
    y="Country Name",
    size="value",
    color="Region",
    title=f"{selected_indicator} - Country Comparison ({year})",
    height=700
)

st.plotly_chart(fig_bubble, use_container_width=True)


# ======================================================
# DATA TABLE
# ======================================================
st.markdown("### 📄 Filtered Dataset")

st.dataframe(latest_df.sort_values("value", ascending=False))
