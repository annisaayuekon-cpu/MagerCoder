# ==========================================
# PERTUMBUHAN EKONOMI, GDP & GNI
# DESCRIPTIVE ANALYSIS
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Pertumbuhan Ekonomi & GDP",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Pertumbuhan Ekonomi, GDP & GNI — Peta Dunia + Time Series")
st.write(
    "Dashboard ini menyajikan indikator ekonomi makro utama berdasarkan data World Bank. "
    "Data telah dibersihkan sehingga **hanya mencakup negara berdaulat**, "
    "tanpa agregat regional atau kelompok pendapatan."
)

# ==========================================
# FILE CONFIG
# ==========================================

DATA_DIR = "data"

FILES = {
    "GDP (Current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per Capita (US$)": "1.2. GDP PER CAPITA.csv",
    "GDP Growth (%)": "1.3. GDP growth (%).csv",
    "Gross National Income (GNI)": "1.4. Gross National Income (GNI).csv",
}

indicator = st.selectbox("📌 Pilih indikator ekonomi:", list(FILES.keys()))
file_path = os.path.join(DATA_DIR, FILES[indicator])

if not os.path.exists(file_path):
    st.error("❌ File tidak ditemukan. Periksa nama file di folder data/")
    st.stop()

# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data
def load_data(path):
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

df = load_data(file_path)

st.subheader("📄 Preview Data")
st.dataframe(df.head(10), use_container_width=True)

# ==========================================
# TRANSFORM WIDE → LONG
# ==========================================

country_col = df.columns[0]
year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]

df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value"
).rename(columns={country_col: "country"})

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["year", "value"])
df_long["country"] = df_long["country"].astype(str).str.strip()

# ==========================================
# FILTER: HANYA NEGARA BERDAULAT
# ==========================================

NON_COUNTRY_KEYWORDS = [
    "income", "world", "oecd", "ibrd", "ida",
    "demographic", "dividend", "area", "union",
    "total", "excluding", "members"
]

df_long = df_long[
    ~df_long["country"].str.lower().str.contains("|".join(NON_COUNTRY_KEYWORDS))
]

# ==========================================
# MAP
# ==========================================

st.subheader("🌍 Peta Dunia")

years = sorted(df_long["year"].unique())
year_select = st.slider("Pilih tahun:", min(years), max(years), max(years))

df_map = df_long[df_long["year"] == year_select]

fig_map = px.choropleth(
    df_map,
    locations="country",
    locationmode="country names",
    color="value",
    hover_name="country",
    color_continuous_scale="Viridis",
    labels={"value": indicator},
    title=f"{indicator} ({year_select})"
)
fig_map.update_layout(height=520)
st.plotly_chart(fig_map, use_container_width=True)

# ==========================================
# TIME SERIES
# ==========================================

st.subheader("📈 Time Series")

countries = sorted(df_long["country"].unique())
default_country = "Indonesia" if "Indonesia" in countries else countries[0]

selected = st.multiselect(
    "Pilih negara:",
    countries,
    default=[default_country]
)

df_ts = df_long[df_long["country"].isin(selected)]

fig_ts = px.line(
    df_ts,
    x="year",
    y="value",
    color="country",
    markers=True,
    title=f"Time Series — {indicator}"
)
st.plotly_chart(fig_ts, use_container_width=True)

# ==========================================
# TOP & BOTTOM
# ==========================================

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

# ==========================================
# ANALISIS DESKRIPTIF
# ==========================================

top_countries = latest.head(5)["country"].tolist()
bottom_countries = latest.tail(5)["country"].tolist()

st.subheader("🧠 Analisis Ekonomi Deskriptif")

st.markdown(f"""
Berdasarkan indikator **{indicator}**, terlihat adanya ketimpangan ekonomi global
yang cukup tajam antar negara.

Negara dengan nilai tertinggi seperti **{", ".join(top_countries)}**
menunjukkan kapasitas ekonomi yang besar dan relatif mapan.

Sebaliknya, negara dengan nilai terendah seperti **{", ".join(bottom_countries)}**
merefleksikan keterbatasan skala ekonomi dan tingkat pendapatan nasional.
""")

if "growth" in indicator.lower():
    st.markdown("""
Pertumbuhan ekonomi yang tinggi tidak selalu mencerminkan kekuatan struktural jangka panjang,
karena dapat dipengaruhi oleh **low base effect**, yaitu pertumbuhan besar akibat basis ekonomi
tahun sebelumnya yang sangat rendah.
""")

st.caption(
    "Catatan: Agregat regional dan kelompok pendapatan (OECD, World, income groups) telah dihapus. "
    "Analisis ini bersifat deskriptif."
)
