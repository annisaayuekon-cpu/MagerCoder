import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="Economic Dashboard",
    layout="wide",
    page_icon="📊",
)

# ==========================
# CUSTOM CSS
# ==========================
st.markdown("""
<style>
.big-title { font-size: 42px; font-weight: 900; color: #1d3557; }
.subtitle { font-size: 17px; color: #457b9d; }
.filter-bar { background: #e8f1fb; padding: 15px; border-radius: 10px; border: 1px solid #c8d9ef; }
.kpi-card { padding: 18px; border-radius: 10px; color: white; font-weight: 600; text-align:center; }
.kpi-number { font-size: 30px; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

DATA_DIR = "data"

# ==========================================
# UNIVERSAL DATA ENGINE
# ==========================================
def robust_csv_loader(path):
    """Smart CSV loader: automatically detects delimiters."""
    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 3:
                return df
        except:
            pass
    return pd.DataFrame()

def convert_wide_to_long(df):
    """Convert wide-format World Bank data to long format."""
    if df.empty:
        return df

    df.columns = df.columns.str.strip()

    # column detection
    country_col = "Country Name" if "Country Name" in df.columns else df.columns[0]
    code_col = "Country Code" if "Country Code" in df.columns else df.columns[1]

    year_cols = [c for c in df.columns if str(c).isdigit()]

    long_df = df.melt(
        id_vars=[country_col, code_col],
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )

    long_df["year"] = pd.to_numeric(long_df["year"], errors="ignore")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df = long_df.dropna(subset=["value"])

    return long_df.rename(columns={country_col: "country", code_col: "code"})


# ==========================================
# REGION MAPPING (WORLD BANK STANDARD)
# ==========================================
REGION_MAP = {
    "East Asia & Pacific": ["CHN","IDN","MYS","SGP","THA","VNM","PHL","KHM","LAO","BRN","MMR","MNG","TLS"],
    "Europe & Central Asia": ["GBR","FRA","DEU","ITA","ESP","NLD","SWE","NOR","FIN","POL","ROU","RUS","UKR","TUR"],
    "Latin America & Caribbean": ["BRA","ARG","CHL","COL","PER","MEX","ECU","URY","PRY","PAN","BOL"],
    "Middle East & North Africa": ["SAU","ARE","QAT","EGY","MAR","DZA","TUN","ISR","JOR","KWT","BHR","OMN","LBY"],
    "North America": ["USA","CAN"],
    "South Asia": ["IND","PAK","BGD","LKA","NPL","BTN","MDV"],
    "Sub-Saharan Africa": ["NGA","ETH","KEN","UGA","GHA","TZA","ZAF","SEN","AGO","CMR","ZMB","ZWE","RWA","MOZ"],
}

ALL_REGIONS = ["Global"] + list(REGION_MAP.keys())


# ==========================================
# AUTO LOAD ALL DATA FILES
# ==========================================
files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
indicator_list = [f.replace(".csv", "") for f in files]
indicator_map = {f.replace(".csv",""): os.path.join(DATA_DIR, f) for f in files}


# ==========================================
# HEADER
# ==========================================
st.markdown("<div class='big-title'>🌍 Economic Visualization Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Interactive dashboard using real World Bank data</div><br>",
            unsafe_allow_html=True)


# ==========================================
# FILTER BAR
# ==========================================
st.markdown("<div class='filter-bar'>", unsafe_allow_html=True)

colA, colB, colC, colD = st.columns([3,2,2,2])

with colA:
    search_country = st.text_input("🔍 Search Country (optional)")

with colB:
    selected_indicator = st.selectbox("📊 Select Indicator", indicator_list)

with colC:
    region_filter = st.selectbox("🌍 Region", ALL_REGIONS)

with colD:
    selected_year = st.slider("📅 Year", 1990, 2024, 2020)

st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# LOAD SELECTED DATA
# ==========================================
df_raw = robust_csv_loader(indicator_map[selected_indicator])
df_long = convert_wide_to_long(df_raw)

# ==========================================
# APPLY REGION FILTER
# ==========================================
if region_filter != "Global":
    valid_codes = REGION_MAP[region_filter]
    df_long = df_long[df_long["code"].isin(valid_codes)]

# ==========================================
# APPLY COUNTRY SEARCH FILTER
# ==========================================
if search_country:
    df_long = df_long[df_long["country"].str.contains(search_country, case=False)]

# Avoid empty data
if df_long.empty:
    st.error("❗ No data available for this filter combination.")
    st.stop()


# ==========================================
# KPI CARDS
# ==========================================
col1, col2, col3, col4 = st.columns(4)

latest_year = df_long["year"].max()
latest_global = df_long[df_long["year"] == latest_year]["value"].mean()

col1.markdown(f"""
<div class='kpi-card' style='background:#1d3557;'>
    <div>Latest Value (Region/Global)</div>
    <div class='kpi-number'>{latest_global:,.2f}</div>
</div>
""", unsafe_allow_html=True)


# KPI: If country searched
if search_country:
    df_country_only = df_long[df_long["country"].str.contains(search_country, case=False)]
    if not df_country_only.empty:
        latest_country = df_country_only.sort_values("year").iloc[-1]["value"]
        col2.markdown(f"""
        <div class='kpi-card' style='background:#2a9d8f;'>
            <div>{search_country}</div>
            <div class='kpi-number'>{latest_country:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col2.markdown("<div class='kpi-card' style='background:#2a9d8f;'>No Country Data</div>",
                      unsafe_allow_html=True)
else:
    col2.markdown("<div class='kpi-card' style='background:#2a9d8f;'>No Country Selected</div>",
                  unsafe_allow_html=True)

col3.markdown(f"""
<div class='kpi-card' style='background:#e76f51;'>
    <div>Total Countries</div>
    <div class='kpi-number'>{df_long['country'].nunique()}</div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div class='kpi-card' style='background:#f4a261;'>
    <div>Dataset Rows</div>
    <div class='kpi-number'>{len(df_long):,}</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# TIME SERIES CHART
# ==========================================
st.subheader("📈 Time Series Trend")

fig_ts = px.line(
    df_long,
    x="year",
    y="value",
    color="country",
    title=f"Trend of {selected_indicator}",
)
st.plotly_chart(fig_ts, use_container_width=True)


# ==========================================
# BUBBLE CHART (Top 20 countries)
# ==========================================
st.subheader("🔵 Country Comparison (Bubble Chart)")

df_year = df_long[df_long["year"] == selected_year].nlargest(20, "value")

fig_bubble = px.scatter(
    df_year,
    x="value",
    y="country",
    size="value",
    hover_name="country",
    title=f"Top Countries ({selected_year}) – {selected_indicator}"
)
st.plotly_chart(fig_bubble, use_container_width=True)


# ==========================================
# WORLD MAP
# ==========================================
st.subheader("🗺 World Map")

fig_map = px.choropleth(
    df_year,
    locations="country",
    locationmode="country names",
    color="value",
    title=f"Global/Regional Distribution ({selected_year})",
)
st.plotly_chart(fig_map, use_container_width=True)

# ==========================================
# DONUT CHART SECTION
# ==========================================
st.subheader("🍩 Indicator Category Breakdown")

df_latest = df_long[df_long["year"] == selected_year]

# ---------------------
# CATEGORY DEFINITIONS
# ---------------------
def categorize_indicator(value, indicator):

    if indicator.startswith("1.1"):  # GDP
        if value < 5e10: return "Low GDP"
        elif value < 5e11: return "Middle GDP"
        elif value < 1e12: return "High GDP"
        else: return "Very High GDP"

    if indicator.startswith("1.2"):  # GDP per capita
        if value < 1000: return "Low Income"
        elif value < 4000: return "Lower Middle"
        elif value < 12000: return "Upper Middle"
        else: return "High Income"

    if indicator.startswith("1.3"):  # GDP growth %
        if value < 0: return "Negative"
        elif value < 3: return "Low"
        elif value < 6: return "Moderate"
        else: return "High"

    if indicator.startswith("3.1"):  # Inflation
        if value > 50: return "Hyperinflation"
        elif value > 10: return "High"
        elif value > 3: return "Moderate"
        else: return "Stable"

    if indicator.startswith("2.2"):  # Unemployment
        if value < 5: return "Low"
        elif value < 10: return "Medium"
        elif value < 15: return "High"
        else: return "Very High"

    if indicator.startswith("5.1"):  # FDI
        if value < 1e9: return "Very Low"
        elif value < 5e9: return "Low"
        elif value < 2e10: return "Medium"
        else: return "High"

    return "Other"


# Apply categorization
df_latest["category"] = df_latest["value"].apply(lambda x: categorize_indicator(x, selected_indicator))

# Create donut chart
donut_df = df_latest.groupby("category")["value"].count().reset_index().rename(columns={"value": "count"})

fig_donut = px.pie(
    donut_df,
    names="category",
    values="count",
    hole=0.5,
    title=f"{selected_indicator} — Category Breakdown ({selected_year})",
)

st.plotly_chart(fig_donut, use_container_width=True)

