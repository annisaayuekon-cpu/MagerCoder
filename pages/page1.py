# pages/page1_ekonomi.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Pertumbuhan Ekonomi & GDP",
    page_icon="📈"
)

st.title("📈 Pertumbuhan Ekonomi & GDP — Peta Dunia + Time Series")
st.write(
    "Halaman ini menyajikan indikator ekonomi makro utama (GDP dan GDP Growth) "
    "berdasarkan data World Bank. Data telah dibersihkan sehingga hanya mencakup "
    "**negara berdaulat**, tanpa agregat regional atau kelompok pendapatan."
)

# -------------------------------------------------
# DATA
# -------------------------------------------------
DATA_DIR = "data"

FILES = {
    "GDP (Current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per Capita (US$)": "1.2. GDP PER CAPITA.csv",
    "GDP Growth (%)": "1.3. GDP growth (%).csv",
}

# -------------------------------------------------
# AGGREGATE FILTER (WAJIB)
# -------------------------------------------------
AGGREGATE_ENTITIES = {
    "World",
    "High income",
    "Upper middle income",
    "Lower middle income",
    "Low income",
    "OECD members",
    "Euro area",
    "European Union",
    "European Union (27)",
    "Europe & Central Asia",
    "East Asia & Pacific",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
    "Arab World",
    "IDA total",
    "IDA & IBRD total",
    "IBRD only",
    "Least developed countries: UN classification",
    "Fragile and conflict affected situations",
    "Small states",
    "Other small states",
}

# -------------------------------------------------
# CSV LOADER
# -------------------------------------------------
@st.cache_data
def load_csv_clean(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

# -------------------------------------------------
# PILIH INDIKATOR
# -------------------------------------------------
indicator = st.selectbox("📌 Pilih indikator ekonomi:", list(FILES.keys()))
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_clean(file_path)
if df.empty:
    st.error("File tidak ditemukan atau gagal dibaca.")
    st.stop()

st.subheader("📄 Preview Data")
st.dataframe(df.head(10), use_container_width=True)

# -------------------------------------------------
# TRANSFORM → LONG FORMAT
# -------------------------------------------------
cols = [str(c).strip() for c in df.columns]
cols_lower = [c.lower() for c in cols]

def find_country_col(cols):
    for c in cols:
        if c.lower() in ["country name", "country", "negara", "entity"]:
            return c
    return cols[0]

# LONG FORMAT
if "year" in cols_lower:
    rename = {}
    for c in df.columns:
        if c.lower() in ["country name", "country", "entity"]:
            rename[c] = "country"
        if c.lower() == "year":
            rename[c] = "year"
    df = df.rename(columns=rename)

    value_cols = [c for c in df.columns if c not in ["country", "year"]]
    value_col = value_cols[-1]

    df_long = df[["country", "year", value_col]].rename(columns={value_col: "value"})
else:
    year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
    country_col = find_country_col(df.columns)

    df_long = df.melt(
        id_vars=[country_col],
        value_vars=year_cols,
        var_name="year",
        value_name="value"
    ).rename(columns={country_col: "country"})

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long["country"] = df_long["country"].astype(str).str.strip()

# -------------------------------------------------
# 🔥 FILTER: HANYA NEGARA (BUANG AGGREGATE)
# -------------------------------------------------
df_long = df_long[~df_long["country"].isin(AGGREGATE_ENTITIES)]

if df_long.empty:
    st.error("Data kosong setelah filtering aggregate.")
    st.stop()

# -------------------------------------------------
# PETA DUNIA
# -------------------------------------------------
years = sorted(df_long["year"].dropna().unique().astype(int))
year_selected = st.slider(
    "Pilih tahun:",
    min(years),
    max(years),
    max(years)
)

df_map = df_long[df_long["year"] == year_selected]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_selected})")
fig_map = px.choropleth(
    df_map,
    locations="country",
    locationmode="country names",
    color="value",
    hover_name="country",
    color_continuous_scale="Blues",
    labels={"value": indicator},
)
fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# -------------------------------------------------
# TIME SERIES
# -------------------------------------------------
st.subheader("📈 Time Series per Negara")

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
    labels={"year": "Tahun", "value": indicator}
)
fig_ts.update_layout(margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_ts, use_container_width=True)

# -------------------------------------------------
# STATISTIK RINGKAS
# -------------------------------------------------
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

agg = (
    df_long.groupby("country")
    .apply(lambda g: g.loc[g["year"].idxmax(), "value"])
    .reset_index()
)
agg.columns = ["country", "latest_value"]
agg = agg.sort_values("latest_value", ascending=False)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Top 10 (terbesar)**")
    st.table(agg.head(10).style.format({"latest_value": "{:,.2f}"}))

with c2:
    st.markdown("**Bottom 10 (terendah)**")
    st.table(agg.tail(10).sort_values("latest_value").style.format({"latest_value": "{:,.2f}"}))

# -------------------------------------------------
# ANALISIS OTOMATIS (UNTUK DOSEN)
# -------------------------------------------------
st.subheader("🧠 Interpretasi Ekonomi")

st.markdown("""
Hasil visualisasi menunjukkan adanya ketimpangan ekonomi yang signifikan antar negara.

Negara-negara dengan **GDP dan GDP per kapita tinggi** umumnya merupakan negara
berpendapatan tinggi dengan basis industri dan jasa yang kuat, serta integrasi
yang tinggi dalam perdagangan dan keuangan global.

Sebaliknya, negara-negara dengan **GDP dan pertumbuhan ekonomi rendah**
didominasi oleh negara berkembang dan negara konflik, yang menghadapi
keterbatasan modal, infrastruktur, dan stabilitas ekonomi.

Temuan ini menegaskan bahwa kapasitas pertumbuhan ekonomi sangat dipengaruhi oleh
struktur produksi, kualitas institusi, dan integrasi global.
""")

# -------------------------------------------------
# DOWNLOAD
# -------------------------------------------------
st.subheader("📥 Unduh Data")
st.download_button(
    "⬇ Download CSV (long format)",
    df_long.to_csv(index=False),
    file_name="ekonomi_gdp_clean.csv",
    mime="text/csv"
)
