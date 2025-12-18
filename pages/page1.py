# ======================================================
# PERTUMBUHAN EKONOMI & GDP — DESKRIPTIF (NEGARA SAJA)
# ======================================================

import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP", page_icon="📈")

st.title("📈 Pertumbuhan Ekonomi & GDP — Peta Dunia + Time Series")
st.markdown(
    """
    Halaman ini menyajikan indikator ekonomi makro utama berdasarkan **World Bank**.
    Data telah **dibersihkan** sehingga **hanya mencakup negara berdaulat**,
    tanpa agregat regional, kelompok pendapatan, maupun institusi.
    """
)

# ======================================================
# FILE MAPPING
# ======================================================

DATA_DIR = "data"

FILES = {
    "GDP (Current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per Capita (US$)": "1.2. GDP PER CAPITA.csv",
    "GDP Growth (%)": "1.3 GDP growth (%).csv",
    "Gross National Income (GNI)": "1.4 Gross National Income (GNI).csv",
}

# ======================================================
# CSV LOADER (AMAN)
# ======================================================

@st.cache_data
def load_csv(path):
    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python")
            if df.shape[1] > 2:
                return df
        except:
            pass
    return pd.DataFrame()

# ======================================================
# PILIH INDIKATOR
# ======================================================

indicator = st.selectbox("📌 Pilih indikator ekonomi:", list(FILES.keys()))
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv(file_path)
if df.empty:
    st.error("❌ File tidak ditemukan atau gagal dibaca.")
    st.stop()

# ======================================================
# TRANSFORMASI → LONG FORMAT
# ======================================================

country_col = df.columns[0]
year_cols = [c for c in df.columns if c.isdigit()]

df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value"
)

df_long = df_long.rename(columns={country_col: "country"})
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["year", "value"])

# ======================================================
# 🔥 FILTER FINAL — HANYA NEGARA BERDAULAT
# ======================================================

EXCLUDE_KEYWORDS = [
    # income & institution
    "income", "oecd", "ibrd", "ida", "world", "bank",

    # demographic
    "demographic", "dividend",

    # regional aggregates
    "asia", "europe", "africa", "america", "pacific",
    "middle east", "caribbean", "north africa",

    # general aggregate
    "union", "area", "total", "excluding", "members"
]

df_long = df_long[
    ~df_long["country"]
    .str.lower()
    .str.contains("|".join(EXCLUDE_KEYWORDS), regex=True)
]

# ======================================================
# PETA DUNIA
# ======================================================

year_latest = int(df_long["year"].max())
df_map = df_long[df_long["year"] == year_latest]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_latest})")

fig_map = px.choropleth(
    df_map,
    locations="country",
    locationmode="country names",
    color="value",
    hover_name="country",
    color_continuous_scale="Viridis",
    labels={"value": indicator}
)

fig_map.update_layout(height=520)
st.plotly_chart(fig_map, use_container_width=True)

# ======================================================
# TIME SERIES
# ======================================================

st.subheader("📈 Time Series per Negara")

countries = sorted(df_long["country"].unique())
default = ["Indonesia"] if "Indonesia" in countries else countries[:1]

selected = st.multiselect(
    "Pilih negara:",
    countries,
    default=default
)

df_ts = df_long[df_long["country"].isin(selected)]

fig_ts = px.line(
    df_ts,
    x="year",
    y="value",
    color="country",
    markers=True,
    labels={"year": "Tahun", "value": indicator}
)

st.plotly_chart(fig_ts, use_container_width=True)

# ======================================================
# STATISTIK RINGKAS (TOP & BOTTOM)
# ======================================================

st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

latest = (
    df_long.groupby("country")
    .apply(lambda g: g.loc[g["year"].idxmax(), "value"])
    .reset_index(name="latest_value")
    .sort_values("latest_value", ascending=False)
)

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Top 10 (terbesar)**")
    st.table(latest.head(10).style.format({"latest_value": "{:,.2f}"}))

with c2:
    st.markdown("**Bottom 10 (terendah)**")
    st.table(latest.tail(10).sort_values("latest_value").style.format({"latest_value": "{:,.2f}"}))

# ======================================================
# ANALISIS DESKRIPTIF SINGKAT
# ======================================================

st.subheader("🧠 Analisis Ekonomi Deskriptif")

top_countries = ", ".join(latest.head(5)["country"])
bottom_countries = ", ".join(latest.tail(5)["country"])

st.markdown(f"""
Berdasarkan nilai terbaru **{indicator}**, terlihat perbedaan yang jelas antar negara.

- **Kelompok nilai tertinggi** didominasi oleh: **{top_countries}**  
- **Kelompok nilai terendah** didominasi oleh: **{bottom_countries}**

Perbedaan ini mencerminkan variasi **skala ekonomi, tingkat pembangunan, serta kapasitas produksi nasional**.
Analisis ini bersifat **deskriptif**, tanpa inferensi kausal.
""")

st.caption(
    "Catatan: Seluruh agregat regional dan kelompok pendapatan World Bank "
    "(OECD, income groups, regional totals) telah dihapus. "
    "Analisis ini murni mencerminkan kinerja negara berdaulat."
)
