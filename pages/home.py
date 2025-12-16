import streamlit as st
import pandas as pd
import plotly.express as px
import os

from region_mapping import get_region

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Dashboard Ekonomi – Ringkasan",
    layout="wide"
)

# =====================================================
# PATH & DATA LOADER
# =====================================================
DATA_DIR = "data"

@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)
    return df

# =====================================================
# HEADER
# =====================================================
st.title("📊 Dashboard Ekonomi Indonesia & Global")
st.caption("Ringkasan indikator utama – gaya World Bank / PPI")

# =====================================================
# SIDEBAR FILTER
# =====================================================
st.sidebar.header("Filter Data")

indicator_files = sorted([
    f for f in os.listdir(DATA_DIR) if f.endswith(".csv")
])

indicator = st.sidebar.selectbox(
    "Indikator",
    indicator_files,
    index=0
)

df = load_csv(indicator)

# Pastikan kolom standar ada
required_cols = {"Country", "Country Code", "Year", "Value"}
if not required_cols.issubset(df.columns):
    st.error(
        f"Struktur CSV tidak sesuai. "
        f"Kolom wajib: {required_cols}"
    )
    st.stop()

countries = sorted(df["Country"].dropna().unique())

selected_countries = st.sidebar.multiselect(
    "Negara",
    countries,
    default=countries[:5]
)

year_min = int(df["Year"].min())
year_max = int(df["Year"].max())

year_range = st.sidebar.slider(
    "Rentang Tahun",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max)
)

# =====================================================
# FILTER DATA
# =====================================================
df_filtered = df[
    (df["Country"].isin(selected_countries)) &
    (df["Year"].between(year_range[0], year_range[1]))
].copy()

df_filtered["Region"] = df_filtered["Country"].apply(get_region)

# =====================================================
# MAIN METRICS
# =====================================================
st.subheader(indicator.replace(".csv", ""))

latest_year = df_filtered["Year"].max()
df_latest = df_filtered[df_filtered["Year"] == latest_year]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Tahun Terakhir",
        latest_year
    )

with col2:
    st.metric(
        "Jumlah Negara",
        df_latest["Country"].nunique()
    )

with col3:
    st.metric(
        "Rata-rata Nilai",
        round(df_latest["Value"].mean(), 2)
    )

# =====================================================
# LINE CHART (TIME SERIES)
# =====================================================
st.markdown("### 📈 Tren Waktu")

fig_line = px.line(
    df_filtered,
    x="Year",
    y="Value",
    color="Country",
    markers=True
)

fig_line.update_layout(
    height=450,
    legend_title_text="Negara"
)

st.plotly_chart(fig_line, use_container_width=True)

# =====================================================
# MAP (WORLD BANK STYLE)
# =====================================================
st.markdown("### 🗺️ Peta Global (Tahun Terakhir)")

fig_map = px.choropleth(
    df_latest,
    locations="Country Code",
    color="Value",
    hover_name="Country",
    color_continuous_scale="Blues"
)

fig_map.update_layout(
    height=500,
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig_map, use_container_width=True)

# =====================================================
# REGION SUMMARY
# =====================================================
st.markdown("### 🌍 Ringkasan per Region")

region_summary = (
    df_latest
    .groupby("Region", as_index=False)["Value"]
    .mean()
    .sort_values("Value", ascending=False)
)

fig_bar = px.bar(
    region_summary,
    x="Region",
    y="Value",
    color="Region"
)

fig_bar.update_layout(
    showlegend=False,
    height=400
)

st.plotly_chart(fig_bar, use_container_width=True)

# =====================================================
# DATA TABLE
# =====================================================
with st.expander("📄 Tampilkan Data"):
    st.dataframe(
        df_filtered.sort_values(["Country", "Year"]),
        use_container_width=True
    )
