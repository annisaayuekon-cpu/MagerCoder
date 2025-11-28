import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📉 Inflasi & Indeks Harga Konsumen (IHK/CPI) — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator **Inflasi** dan **Indeks Harga Konsumen (IHK/CPI)** "
    "berdasarkan file CSV yang berada pada folder `data/`. Format file mengikuti nama seperti di bawah."
)

# -----------------------------
# Folder data & daftar file CSV
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Inflation annual (%)": "3.1 Inflation annual percent.csv",
    "Consumer Price Index (CPI)": "3.2 CPI index.csv",
    "Inflation food prices (%)": "3.3 Inflation food.csv",
    "Inflation core rate (%)": "3.4 Core inflation.csv",
}

# -----------------------------
# Loader CSV fleksibel
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

# -----------------------------
# Cek file yang tersedia
# -----------------------------
available_files = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_files.append(label)

if not available_files:
    st.error(f"Tidak ada file CSV Page 3 ditemukan dalam folder `{DATA_DIR}/`.")
    st.stop()

# -----------------------------
# Pilih indikator + Load data
# -----------------------------
indicator = st.selectbox("📌 Pilih indikator inflasi / CPI :", available_files)

file_path = os.path.join(DATA_DIR, FILES[indicator])

try:
    df = load_csv_clean(file_path)
except Exception as e:
    st.error(f"❌ File gagal dibaca: `{os.path.basename(file_path)}`\n\nError: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Identifikasi kolom Tahun dan Negara
# -----------------------------
cols = [str(c) for c in df.columns]
years = [c for c in cols if c.isdigit() and len(c) == 4]

if not years:
    st.error("Tidak ditemukan kolom tahun (misal 1990, 2005 dst.) — periksa header CSV.")
    st.stop()

country_col = next((c for c in df.columns if c in 
                   ["Country Name","Country","Negara","Entity","country"]), df.columns[0])

# Convert ke long format
df_long = df.melt(id_vars=[country_col], value_vars=years,
                  var_name="year", value_name="value")

df_long["year"] = pd.to_numeric(df_long["year"], errors="ignore")
df_long = df_long.rename(columns={country_col:"country"}).dropna(subset=["value"])

if df_long.empty:
    st.error("Data kosong setelah transformasi long — kemungkinan format tidak sesuai.")
    st.stop()

# -----------------------------
# Pilih tahun untuk peta dunia
# -----------------------------
years_sorted = sorted(df_long["year"].unique())
year_select = st.slider("Pilih tahun untuk peta dunia :", int(min(years_sorted)), int(max(years_sorted)), int(max(years_sorted)))

df_map = df_long[df_long["year"] == year_select]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_select})")

if df_map.empty:
    st.warning("Tidak ada data pada tahun ini.")
else:
    try:
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            color_continuous_scale="Turbo",
            hover_name="country",
            title=f"{indicator} — {year_select}",
        )
        fig.update_layout(margin={"r":0,"l":0,"t":30,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Peta gagal dibuat. Cek kesesuaian nama negara.\n\n{e}")

# -----------------------------
# Grafik Time Series
# -----------------------------
st.subheader("📈 Tren Time Series per Negara")

country_list = sorted(df_long["country"].unique().tolist())
selected_country = st.selectbox("Pilih negara grafik :", country_list)

df_country = df_long[df_long["country"] == selected_country]

if df_country.empty:
    st.info("Tidak ada time series untuk negara ini.")
else:
    st.line_chart(df_country.set_index("year")["value"], height=350)
    st.dataframe(df_country.reset_index(drop=True), use_container_width=True)

# -----------------------------
# Download Full Data
# -----------------------------
st.subheader("📥 Ekspor Data")
csv = df_long.to_csv(index=False)
st.download_button(
    label="⬇ Download CSV",
    data=csv,
    file_name=f"inflasi_cpi_{indicator.replace(' ','_')}.csv",
    mime="text/csv"
)
