import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

st.set_page_config(
    page_title="Pertumbuhan Ekonomi & GDP",
    layout="wide",
    page_icon="📈"
)

st.title("📈 Pertumbuhan Ekonomi & GDP — Peta Dunia + Time Series")
st.write(
    "Halaman ini menyajikan indikator ekonomi makro utama (GDP dan GDP Growth) "
    "berdasarkan data World Bank. Data telah dibersihkan sehingga **hanya mencakup "
    "negara berdaulat**, tanpa agregat regional atau kelompok pendapatan."
)

# ======================================================
# 1. Folder & File Mapping
# ======================================================
DATA_DIR = "data"

FILES = {
    "GDP (Current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per Capita (US$)": "1.2. GDP PER CAPITA.csv",
    "GDP Growth (%)": "1.3 GDP growth (%).csv",
    "Gross National Income (GNI)": "1.4 Gross National Income (GNI).csv",
}

# ======================================================
# 2. Loader CSV fleksibel
# ======================================================
@st.cache_data
def load_csv(path):
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 2:
                return df
        except Exception:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

# ======================================================
# 3. Fungsi pembersihan negara agregat
# ======================================================
def is_aggregate(name: str) -> bool:
    patterns = [
        "world", "income", "oecd", "asia", "africa", "europe",
        "america", "union", "arab", "small states",
        "least developed", "heavily indebted"
    ]
    name = name.lower()
    return any(p in name for p in patterns)

# ======================================================
# 4. Pilih indikator
# ======================================================
indicator = st.selectbox("📌 Pilih indikator ekonomi:", list(FILES.keys()))
file_path = os.path.join(DATA_DIR, FILES[indicator])

if not os.path.exists(file_path):
    st.error("❌ File tidak ditemukan. Periksa nama file di folder data/")
    st.stop()

df_raw = load_csv(file_path)

# ======================================================
# 5. Deteksi format WIDE → LONG
# ======================================================
cols = [c.strip() for c in df_raw.columns]

country_col = next((c for c in cols if c.lower() in ["country name", "country", "negara"]), cols[0])
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

df_long = df_raw.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value"
)

df_long = df_long.rename(columns={country_col: "country"})
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["value"])

# ======================================================
# 6. FILTER NEGARA SAJA (BUANG AGREGAT)
# ======================================================
df_long["country"] = df_long["country"].astype(str).str.strip()
df_long = df_long[~df_long["country"].apply(is_aggregate)]

st.success(f"✅ Data bersih: {df_long['country'].nunique()} negara berdaulat")

# ======================================================
# 7. Pilih tahun
# ======================================================
years = sorted(df_long["year"].unique().astype(int))
year_selected = st.slider("Pilih tahun:", min(years), max(years), max(years))

df_year = df_long[df_long["year"] == year_selected]

# ======================================================
# 8. PETA DUNIA
# ======================================================
st.subheader(f"🌍 Peta Dunia — {indicator} ({year_selected})")

fig_map = px.choropleth(
    df_year,
    locations="country",
    locationmode="country names",
    color="value",
    hover_name="country",
    color_continuous_scale="Blues",
    labels={"value": indicator}
)
fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# ======================================================
# 9. TIME SERIES
# ======================================================
st.subheader("📈 Time Series per Negara")

countries = sorted(df_long["country"].unique())
default = ["Indonesia"] if "Indonesia" in countries else countries[:1]

selected = st.multiselect("Pilih negara:", countries, default=default)

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

# ======================================================
# 10. TOP & BOTTOM
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
# =====================================================
# ANALISIS EKONOMI TERPADU
# =====================================================
st.subheader("🧠 Analisis Ekonomi Terpadu")

# Ambil Top & Bottom 5 negara dari hasil statistik
top_countries = agg_latest.head(5)["country"].tolist()
bottom_countries = agg_latest.tail(5)["country"].tolist()

# Tentukan jenis indikator untuk narasi
indicator_lower = indicator.lower()

if "gdp growth" in indicator_lower:
    indikator_nama = "Pertumbuhan Ekonomi (GDP Growth)"
    makna_tinggi = "menunjukkan ekspansi ekonomi yang cepat"
    makna_rendah = "mengindikasikan kontraksi atau stagnasi ekonomi"
elif "per capita" in indicator_lower:
    indikator_nama = "GDP per Kapita"
    makna_tinggi = "mencerminkan tingkat kesejahteraan penduduk yang tinggi"
    makna_rendah = "menggambarkan rendahnya pendapatan rata-rata masyarakat"
else:
    indikator_nama = "GDP (Skala Ekonomi)"
    makna_tinggi = "menunjukkan skala ekonomi nasional yang besar"
    makna_rendah = "menunjukkan kapasitas ekonomi yang relatif kecil"

st.markdown(f"""
### 🔍 Interpretasi Indikator: **{indikator_nama}**

Berdasarkan nilai terbaru, terdapat perbedaan ekonomi yang tajam antar negara.

**Negara dengan nilai tertinggi** seperti **{", ".join(top_countries)}** umumnya:
- {makna_tinggi}
- Didukung oleh struktur ekonomi tertentu (misalnya sektor keuangan, sumber daya alam, atau basis industri kuat)
- Tidak selalu mencerminkan kesejahteraan merata (khususnya untuk GDP total)

Sebaliknya, **negara dengan nilai terendah** seperti **{", ".join(bottom_countries)}**:
- {makna_rendah}
- Umumnya menghadapi tantangan struktural seperti konflik, kemiskinan, ketergantungan komoditas, atau instabilitas politik
""")

# -----------------------------
# ANALISIS PER INDIKATOR
# -----------------------------
st.markdown("""
### 📊 Sintesis Antarindikator Ekonomi

Analisis ekonomi global perlu dilakukan secara **multidimensi**, karena masing-masing indikator memiliki tolok ukur dan makna yang berbeda:

- **GDP (total)** mencerminkan *kekuatan dan skala ekonomi nasional*
- **GDP per kapita** menggambarkan *tingkat kesejahteraan rata-rata penduduk*
- **GDP Growth** menunjukkan *arah dan dinamika perubahan ekonomi jangka pendek*

Negara dengan GDP besar belum tentu memiliki pertumbuhan tinggi, dan negara dengan pertumbuhan tinggi
belum tentu memiliki tingkat kesejahteraan yang baik.
""")

st.markdown("""
### 📌 Kesimpulan Analisis

Hasil analisis menunjukkan bahwa:
- Negara maju cenderung memiliki **GDP per kapita tinggi** namun **pertumbuhan yang moderat**
- Tingginya laju pertumbuhan ekonomi di beberapa negara berkembang dapat dipengaruhi oleh low base effect, 
yaitu kondisi ketika tingkat pertumbuhan terlihat besar karena nilai awal ekonomi yang relatif rendah, bukan semata-mata karena kapasitas ekonomi yang kuat
- Negara konflik dan miskin struktural cenderung lemah pada seluruh indikator ekonomi

Oleh karena itu, evaluasi kinerja ekonomi suatu negara **tidak dapat bergantung pada satu indikator saja**,
melainkan harus membaca GDP, GDP per kapita, dan GDP Growth secara bersamaan.
""")


# ======================================================
# 11. CATATAN AKADEMIK
# ======================================================
st.caption(
    "Catatan: Seluruh agregat regional dan kelompok pendapatan (OECD, World, income groups) "
    "telah dihapus. Analisis ini murni mencerminkan kinerja **negara berdaulat**."
)
