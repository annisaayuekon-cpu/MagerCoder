import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🔥 Inflasi dan Harga Konsumen — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan data Inflasi dan Harga Konsumen dalam bentuk peta dunia dan grafik time series "
)

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Inflation and consumer": "3.1 Inflation, consumer prices (%).csv",
    "CONSUMER EXPENDITURE": "3.2 CONSUMER EXPENDITURE.csv",
}

# -----------------------------
# Helper: load CSV
# -----------------------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

# cek file mana yang benar-benar ada
available_indicators = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_indicators.append(label)

if not available_indicators:
    st.error(f"Tidak ada file CSV untuk Page 2 yang ditemukan di folder `{DATA_DIR}/`.")
    st.stop()

# -----------------------------
# Pilih indikator
# -----------------------------
indicator_label = st.selectbox("Pilih indikator tenaga kerja/pengangguran", available_indicators)
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

# -----------------------------
# Load data
# -----------------------------
try:
    df = load_csv(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & kolom negara
# -----------------------------
cols = [str(c) for c in df.columns]

# kolom tahun = nama kolom berupa angka 4 digit
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

if not year_cols:
    st.error("Tidak ditemukan kolom tahun (misalnya 1990, 2000, dst.) di file CSV ini.")
    st.stop()

# deteksi kolom nama negara
country_col = None
for cand in ["Country Name", "country", "Country", "Negara"]()