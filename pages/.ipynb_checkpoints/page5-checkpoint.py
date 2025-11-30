# pages/page5.py

import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("💰 Investasi & Pembentukan Modal — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator terkait investasi dan pembentukan modal "
    "berdasarkan data referensi lokal (file CSV) yang ada di folder `data/`."
)

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Foreign direct investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
    "Gross capital formation": "5.2 Gross capital formation.csv",
}

# -----------------------------
# Helper baca CSV (lebih toleran)
# -----------------------------
@st.cache_data
def load_csv_tolerant(path: str) -> pd.DataFrame:
    """
    Coba baca CSV dengan beberapa delimiter dan lewati baris bermasalah.
    """
    # Coba dengan ; , dan tab
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                engine="python",
                on_bad_lines="skip",  # baris yang sangat kacau akan dilewati
            )
            # kalau cuma 1 kolom besar, mungkin delimiter-nya bukan itu
            if df.shape[1] > 1:
                return df
        except Exception:
            continue

    # Fallback: biarkan pandas tebak sendiri
    df = pd.read_csv(
        path,
        engine="python",
        on_bad_lines="skip",
    )
    return df


# -----------------------------
# Cek file yang tersedia
# -----------------------------
available_indicators = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_indicators.append(label)

if not available_indicators:
    st.error(
        f"Tidak ada file CSV Page 5 yang ditemukan di folder `{DATA_DIR}/`. "
        "Pastikan file 5.1 dan 5.2 sudah diletakkan di sana."
    )
    st.stop()

# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox(
    "Pilih indikator investasi/pembentukan modal", available_indicators
)
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & negara
# -----------------------------
cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

if not year_cols:
    st.error(
        "Tidak ditemukan kolom tahun (misalnya 1990, 2000, dst.) "
        "di file CSV ini. Cek kembali header kolom."
    )
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break

if country_col is None:
    # fallback: kolom pertama dianggap nama negara
    country_col = df.columns[0]

# Ubah ke format long: country, year, value
df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value",
)

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce").astype("Int64")
df_long = df_long.rename(columns={country_col: "country"})
df_long = df_long.dropna(subset=["value", "year"])

if df_long.empty:
    st.error("Setelah transformasi, tidak ada data bernilai (semua NaN).")
    st.stop()

# pastikan year integer biasa untuk slider
df_long["year"] = df_long["year"].astype(int)

# -----------------------------
# Slider tahun untuk peta
# -----------------------------
years = sorted(df_long["year"].unique())
year_min = int(min(years))
year_max = int(max(years))

selected_year = st.slider(
    "Pilih tahun untuk peta dunia", year_min, year_max, year_max
)

df_map = df_long[df_long["year"] == selected_year]

st.subheader(f"🌍 Peta Dunia — {indicator_label} ({selected_year})")

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale="Viridis",
            title=f"{indicator_label} — {selected_year}",
            labels={"value": indicator_label},
        )
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(
            "Gagal membuat peta dunia. "
            "Cek apakah nama negara di CSV sesuai standar country names Plotly.\n\n"
            f"Detail error: {e}"
        )

# -----------------------------
# Time series per negara
# -----------------------------
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
selected_country = st.selectbox(
    "Pilih negara untuk grafik time series", country_list
)

df_country = (
    df_long[df_long["country"] == selected_country]
    .sort_values("year")
)

if df_country.empty:
    st.write("Tidak ada data time series untuk negara ini.")
else:
    fig_ts = px.line(
        df_country,
        x="year",
        y="value",
        markers=True,
        title=f"{indicator_label} — {selected_country}",
    )
    fig_ts.update_layout(
        xaxis_title="Tahun",
        yaxis_title=indicator_label,
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    st.dataframe(df_country.reset_index(drop=True))

# -----------------------------
# Tabel lengkap & download
# -----------------------------
st.subheader("📘 Data Lengkap (long format)")
st.dataframe(df_long.reset_index(drop=True), use_container_width=True)

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page5_investment_{indicator_label.replace(' ', '_')}.csv",
    mime="text/csv",
)
