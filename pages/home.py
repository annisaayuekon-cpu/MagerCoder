import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Economic Visualization Dashboard",
    page_icon="🌍",
    layout="wide"
)

# =========================
# STYLE (PPI CLEAN)
# =========================
st.markdown("""
<style>
body { background-color: #f5f7fb; }
.kpi {
    background: white;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.06);
}
.kpi h2 { margin: 0; }
hr { border: 2px solid #1f77b4; }
</style>
""", unsafe_allow_html=True)

# =========================
# INDICATOR CONFIG
# =========================
INDICATORS = {
    "📈 Pertumbuhan Ekonomi & GDP": {
        "GDP Growth (%)": "1.3 GDP growth (%).csv"
    },
    "👷 Tenaga Kerja": {
        "Unemployment Rate (%)": "2.2 Unemployment rate.csv"
    },
    "🔥 Inflasi": {
        "Inflation (%)": "3.1 Inflation, consumer prices (%).csv"
    },
    "🌍 Perdagangan": {
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

# =========================
# ROBUST CSV LOADER (ANTI ERROR)
# =========================
@st.cache_data
def load_indicator(filename):
    path = os.path.join(DATA_DIR, filename)

    try:
        df = pd.read_csv(
            path,
            sep=None,                # AUTO delimiter
            engine="python",
            encoding="utf-8",
            on_bad_lines="skip"
        )
    except Exception:
        df = pd.read_csv(
            path,
            sep=None,
            engine="python",
            encoding="latin1",
            on_bad_lines="skip"
        )

    # Normalisasi nama kolom
    df.columns = df.columns.str.strip()

    if "Country Name" not in df.columns or "Country Code" not in df.columns:
        st.error(f"❌ Format tidak valid: {filename}")
        st.stop()

    df = df.rename(columns={
        "Country Name": "country",
        "Country Code": "code"
    })

    # Ambil kolom tahun saja
    year_cols = [c for c in df.columns if c.isdigit()]
    df = df[["country", "code"] + year_cols]

    # Wide → Long
    df = df.melt(
        id_vars=["country", "code"],
        var_name="year",
        value_name="value"
    )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df.dropna(subset=["year"])

# =========================
# HEADER
# =========================
st.title("🌍 Economic Visualization Dashboard")
st.caption("Interactive dashboard using World Bank data (PPI Style)")

# =========================
# FILTER BAR
# =========================
c1, c2, c3 = st.columns([3, 3, 2])

with c1:
    search = st.text_input("🔍 Search Country (optional)")

with c2:
    category = st.selectbox("📂 Indicator Category", list(INDICATORS.keys()))
    indicator_label = st.selectbox(
        "📊 Indicator",
        list(INDICATORS[category].keys())
    )

with c3:
    year = st.slider("📅 Year", 1990, 2024, 2022)

# =========================
# LOAD DATA
# =========================
df = load_indicator(INDICATORS[category][indicator_label])

if search:
    df = df[df["country"].str.contains(search, case=False, na=False)]

df_year = df[df["year"] == year]

# =========================
# KPI
# =========================
st.markdown("<hr>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)

with k1:
    st.markdown(f"<div class='kpi'><p>Countries</p><h2>{df_year['country'].nunique()}</h2></div>", unsafe_allow_html=True)

with k2:
    st.markdown(f"<div class='kpi'><p>Average Value</p><h2>{df_year['value'].mean():,.2f}</h2></div>", unsafe_allow_html=True)

with k3:
    st.markdown(f"<div class='kpi'><p>Indicator</p><h2>{indicator_label}</h2></div>", unsafe_allow_html=True)

# =========================
# TIME SERIES
# =========================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("📈 Time Series")

fig_ts = px.line(
    df,
    x="year",
    y="value",
    color="country"
)
st.plotly_chart(fig_ts, use_container_width=True)

# =========================
# TOP & BOTTOM
# =========================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🏆 Top & Bottom 10 Countries")

top10 = df_year.sort_values("value", ascending=False).head(10)
bottom10 = df_year.sort_values("value").head(10)

c1, c2 = st.columns(2)
c1.dataframe(top10[["country", "value"]])
c2.dataframe(bottom10[["country", "value"]])

# =========================
# BUBBLE CHART
# =========================
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

# =========================
# MAP
# =========================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🗺 Global Map")

fig_map = px.choropleth(
    df_year,
    locations="code",
    color="value",
    hover_name="country",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_map, use_container_width=True)

# =========================
# EXPORT
# =========================
st.download_button(
    "📥 Download Filtered Data",
    df.to_csv(index=False),
    file_name=f"{indicator_label}.csv"
)
