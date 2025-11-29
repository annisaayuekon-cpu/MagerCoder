import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.markdown("""
<style>

/* ====== BACKGROUND GRADIENT (PAGE) ====== */

/* Kontainer utama aplikasi */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #ffd98a 0%, #ffb07a 50%, #ff7e7e 100%) !important;
    background-attachment: fixed;
}

/* Hilangkan background putih default */
[data-testid="stAppViewContainer"] .main {
    background-color: transparent !important;
}

/* Sidebar juga gradient (opsional, bisa kamu hapus) */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffe1a8, #ffb07a);
}

/* ====== TABLE STYLING ====== */

/* wrapper DataFrame */
[data-testid="stDataFrame"] > div[role="region"] {
  background: rgba(255,255,255,0.75) !important;
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}

/* header tabel */
[data-testid="stDataFrame"] th {
  background: rgba(250,250,250,0.9) !important;
  color: #222 !important;
}

/* baris tabel */
[data-testid="stDataFrame"] td {
  background: rgba(255,255,255,0.85) !important;
}

/* Judul */
h1, h2, h3 {
  color: #1b2733 !important;
}

</style>
""", unsafe_allow_html=True)

# ---- akhir CSS ----

st.title("📉 Inflasi & Indeks Harga Konsumen — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator **Inflasi** dan **Indeks Harga Konsumen (IHK/CPI)** "
    "berdasarkan file CSV yang berada pada folder `data/`. Format file mengikuti nama seperti di bawah."
)

# -----------------------------
# Folder data & daftar file CSV
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Inflation and consumer prices": "3.1 Inflation, consumer prices (%).csv",
    "Consumer Expenditur": "3.2. CONSUMER EXPENDITURE.csv",
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
st.subheader("📈 Grafik Time Series Inflasi / CPI")

# daftar negara
country_list = sorted(df_long["country"].dropna().unique().tolist())

# default: kalau ada Indonesia, pilih itu; kalau tidak, pilih negara pertama
default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]

# boleh pilih satu atau beberapa negara (seperti tombol Also Show di World Bank)
selected_countries = st.multiselect(
    "Pilih negara (bisa lebih dari satu):",
    country_list,
    default=[default_country],
)

# filter data
df_ts = (
    df_long[df_long["country"].isin(selected_countries)]
    .sort_values(["country", "year"])
)

if df_ts.empty:
    st.info("Tidak ada data time series untuk negara yang dipilih.")
else:
    # line chart + titik (markers) seperti di situs World Bank
    fig_ts = px.line(
        df_ts,
        x="year",
        y="value",
        color="country",
        markers=True,  # muncul titik-titik di setiap tahun
        labels={
            "year": "Tahun",
            "value": indicator,
            "country": "Negara",
        },
    )
    # supaya sumbu X rapi (misal loncat 5 tahun)
    fig_ts.update_layout(
        xaxis_title="Tahun",
        yaxis_title=indicator,
        xaxis=dict(dtick=5),
        legend_title="Negara",
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
    )

    st.plotly_chart(fig_ts, use_container_width=True)

    # tabel data yang dipakai grafik
    st.dataframe(
        df_ts.sort_values(["country", "year"]).reset_index(drop=True),
        use_container_width=True,
    )

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
